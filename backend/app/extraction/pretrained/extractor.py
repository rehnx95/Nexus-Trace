import hashlib
from pathlib import PurePath

from app.extraction.common.cdr import parse_cdr
from app.extraction.common.patterns.account import extract_accounts
from app.extraction.common.phone import extract_phones
from app.extraction.common.plate import extract_plates
from app.extraction.common.tabular.financial import parse_financial
from app.extraction.contract.extractor import Extractor
from app.extraction.contract.schemas import Edge, Entity, ExtractionResult, Mention
from app.extraction.pretrained.ner import NerExtractor
from app.extraction.pretrained.relations import RelationExtractor


class PretrainedFirstExtractor(Extractor):
    def __init__(self, ner_extractor: NerExtractor | None = None):
        self.ner_extractor = ner_extractor or NerExtractor()
        self.relation_extractor = RelationExtractor()

    def extract(self, documents: list[dict]) -> ExtractionResult:
        entities: dict[tuple[str, str], Entity] = {}
        edges = []
        diagnostics = {
            "documents": [],
            "phones": 0,
            "plates": 0,
            "accounts": 0,
            "cdr_valid_rows": 0,
            "financial_valid_rows": 0,
            "transactions": [],
        }

        for document in documents:
            filename = document["filename"]
            text = document["text"]
            document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
            extension = PurePath(filename).suffix.lower()
            diagnostics["documents"].append(
                {
                    "filename": filename,
                    "document_id": document_id,
                    "extension": extension,
                }
            )

            if extension in {".csv", ".tsv"}:
                cdr_entities, cdr_edges, cdr_diagnostics = parse_cdr(text, document_id)
                if cdr_diagnostics["format"] != "unsupported":
                    for entity in cdr_entities:
                        entities[(entity.type, entity.id)] = entity
                    edges.extend(cdr_edges)
                    diagnostics["cdr_valid_rows"] += cdr_diagnostics["valid_rows"]
                    diagnostics["cdr_" + document_id] = cdr_diagnostics
                else:
                    account_entities, transactions, financial_diagnostics = parse_financial(
                        text, document_id
                    )
                    for account in account_entities:
                        entity = Entity(
                            type=account["type"],
                            id=account["id"],
                            properties={"account_number": account["id"], "kind": account["kind"]},
                        )
                        entities[(entity.type, entity.id)] = entity
                    diagnostics["accounts"] += len(account_entities)
                    diagnostics["financial_valid_rows"] += financial_diagnostics["valid_rows"]
                    diagnostics["financial_" + document_id] = financial_diagnostics
                    diagnostics["transactions"].extend(transactions)
                    aggregated: dict[tuple[str, str], dict] = {}
                    for transaction in transactions:
                        key = (
                            transaction["from_account"],
                            transaction["to_account"],
                        )
                        amount = float(transaction["amount"])
                        timestamp = transaction.get("timestamp")
                        if key not in aggregated:
                            aggregated[key] = {
                                "total_amount": amount,
                                "txn_count": 1,
                                "first_seen": timestamp,
                                "last_seen": timestamp,
                            }
                        else:
                            row = aggregated[key]
                            row["total_amount"] += amount
                            row["txn_count"] += 1
                            if timestamp:
                                row["last_seen"] = timestamp
                    for (source, target), properties in aggregated.items():
                        properties["total_amount"] = round(properties["total_amount"], 2)
                        edges.append(Edge(
                            source_type="BankAccount",
                            source_id=source,
                            target_type="BankAccount",
                            target_id=target,
                            type="FINANCIAL_TRAIL",
                            properties=properties,
                            evidence=(
                                Mention(
                                    "table-row",
                                    0,
                                    0,
                                    "table",
                                    1.0,
                                    "FINANCIAL-TRANSACTION",
                                    document_id,
                                ),
                            ),
                            confidence=1.0,
                        ))
                continue

            phone_entities, phone_mentions = extract_phones(text, document_id)
            plate_entities, plate_mentions = extract_plates(text, document_id)
            for entity_dict in phone_entities:
                def normalized_phone(raw_text: str) -> str:
                    digits = "".join(character for character in raw_text if character.isdigit())
                    if len(digits) == 10:
                        return "+91" + digits
                    if len(digits) == 12 and digits.startswith("91"):
                        return "+" + digits
                    if len(digits) == 11 and digits.startswith("0"):
                        return "+91" + digits[1:]
                    return ""

                mention = next(
                    item
                    for item in phone_mentions
                    if normalized_phone(item.text) == entity_dict["id"]
                )
                entity = Entity(
                    type=entity_dict["type"],
                    id=entity_dict["id"],
                    properties=entity_dict["properties"],
                    mentions=(mention,),
                )
                entities[(entity.type, entity.id)] = entity
            diagnostics["phones"] += len(phone_entities)

            for entity_dict in plate_entities:
                mention = next(
                    item
                    for item in plate_mentions
                    if "".join(character for character in item.text.upper() if character.isalnum())
                    == entity_dict["id"]
                )
                entity = Entity(
                    type=entity_dict["type"],
                    id=entity_dict["id"],
                    properties=entity_dict["properties"],
                    mentions=(mention,),
                )
                entities[(entity.type, entity.id)] = entity
            diagnostics["plates"] += len(plate_entities)

            ner_entities, ner_status = self.ner_extractor.extract(text, document_id)
            for entity in ner_entities:
                entities[(entity.type, entity.id)] = entity
            diagnostics["ner_" + document_id] = ner_status

            text_accounts = extract_accounts(text)
            for account in text_accounts:
                start = text.find(account["text"])
                mention = Mention(
                    account["text"],
                    start,
                    start + len(account["text"]),
                    "regex",
                    0.99,
                    "IN-BANK-ACCOUNT" if account["kind"] == "account" else "IN-UPI",
                    document_id,
                )
                entity = Entity(
                    type="BankAccount",
                    id=account["id"],
                    properties={"account_number": account["id"], "kind": account["kind"]},
                    mentions=(mention,),
                )
                entities[(entity.type, entity.id)] = entity
            diagnostics["accounts"] += len({account["id"] for account in text_accounts})
            edges.extend(
                self.relation_extractor.extract(text, list(entities.values()), document_id)
            )

        return ExtractionResult(
            entities=list(entities.values()),
            edges=edges,
            diagnostics=diagnostics,
        )
