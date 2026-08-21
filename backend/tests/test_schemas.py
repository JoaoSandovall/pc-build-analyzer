from decimal import Decimal
import unittest

from pydantic import ValidationError

from schemas import ExtractionResult, UploadRequest


class ExtractionSchemaTests(unittest.TestCase):
    def test_accepts_valid_extraction_and_preserves_decimal_price(self):
        result = ExtractionResult.model_validate(
            {
                "valor_total_orcamento": 9999.99,
                "itens": [
                    {
                        "descricao_original": "  RTX 4060   8GB ",
                        "categoria": "GPU",
                        "preco_orcamento": "2499.90",
                    }
                ],
            }
        )

        self.assertEqual(result.itens[0].descricao_original, "RTX 4060 8GB")
        self.assertEqual(result.itens[0].preco_orcamento, Decimal("2499.90"))

    def test_rejects_zero_price_invalid_category_and_extra_item_fields(self):
        with self.assertRaises(ValidationError):
            ExtractionResult.model_validate(
                {
                    "itens": [
                        {
                            "descricao_original": "Produto",
                            "categoria": "MONITOR",
                            "preco_orcamento": 0,
                            "ignorar": True,
                        }
                    ]
                }
            )

    def test_rejects_empty_item_list(self):
        with self.assertRaises(ValidationError):
            ExtractionResult.model_validate({"itens": []})


class UploadSchemaTests(unittest.TestCase):
    def test_rejects_a_path_instead_of_a_file_name(self):
        with self.assertRaises(ValidationError):
            UploadRequest.model_validate({"nome_arquivo": "../orcamento.pdf"})

    def test_accepts_plain_file_name(self):
        request = UploadRequest.model_validate({"nome_arquivo": "orcamento.pdf"})
        self.assertEqual(request.nome_arquivo, "orcamento.pdf")


if __name__ == "__main__":
    unittest.main()
