import os
import unittest
from decimal import Decimal
from unittest.mock import patch

import requests

from scraper import (
    ScrapingError,
    _parse_preco_brl,
    _parse_resultados,
    _similaridade,
    buscar_preco_terabyte,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _ler_fixture(nome: str) -> str:
    with open(os.path.join(FIXTURES_DIR, nome), encoding="utf-8") as f:
        return f.read()


class ParsePrecoBrlTests(unittest.TestCase):
    def test_converte_preco_com_milhar_e_centavos(self):
        self.assertEqual(_parse_preco_brl("R$ 2.399,90"), Decimal("2399.90"))

    def test_converte_preco_sem_milhar(self):
        self.assertEqual(_parse_preco_brl("R$ 89,90"), Decimal("89.90"))

    def test_prioriza_valor_apos_por_quando_ha_desconto(self):
        self.assertEqual(
            _parse_preco_brl("De: R$ 2.599,90 por: R$ 2.399,90"), Decimal("2399.90")
        )

    def test_retorna_none_para_texto_sem_preco(self):
        self.assertIsNone(_parse_preco_brl("Indisponível"))


class SimilaridadeTests(unittest.TestCase):
    def test_termos_em_comum_geram_similaridade_alta(self):
        score = _similaridade(
            "RTX 4060 Ti 8GB Gigabyte",
            "Placa de Vídeo RTX 4060 Ti 8GB Gigabyte Gaming OC",
        )
        self.assertGreater(score, 0.7)

    def test_produtos_diferentes_geram_similaridade_baixa(self):
        score = _similaridade("RTX 4060 Ti 8GB Gigabyte", "Mouse Gamer RGB Qualquer Marca")
        self.assertLess(score, 0.2)

class ParseResultadosTests(unittest.TestCase):
    def test_extrai_apenas_cards_disponiveis_da_fixture(self):
        html = _ler_fixture("terabyte_busca_rtx4060.html")
        resultados = _parse_resultados(html, "https://www.terabyteshop.com.br", "Terabyte")

        self.assertEqual(len(resultados), 1)
        nomes = [r["nome"] for r in resultados]
        self.assertIn("Placa de Vídeo RTX 4060 Ti 8GB Gigabyte Gaming OC", nomes)
        self.assertNotIn("Placa de Vídeo RTX 4060 8GB Asus Dual", nomes)

        primeiro = resultados[0]
        self.assertEqual(primeiro["preco"], Decimal("2399.90"))
        self.assertTrue(
            primeiro["url"].startswith("https://www.terabyteshop.com.br/produto/")
        )
        self.assertEqual(primeiro["loja"], "Terabyte")

    def test_retorna_lista_vazia_quando_nao_ha_cards(self):
        self.assertEqual(_parse_resultados("<html><body>sem resultados</body></html>", "http://mock.com", "MockLoja"), [])

class BuscarPrecoTerabyteTests(unittest.TestCase):
    @patch("scraper._buscar_html")
    def test_escolhe_o_resultado_mais_similar_a_descricao(self, mock_buscar_html):
        mock_buscar_html.return_value = _ler_fixture("terabyte_busca_rtx4060.html")

        resultado = buscar_preco_terabyte("Placa de Vídeo RTX 4060 Ti 8GB Gigabyte")

        self.assertIsNotNone(resultado)
        self.assertEqual(resultado.preco, Decimal("2399.90"))
        self.assertEqual(resultado.loja, "Terabyte")
        self.assertIn("gigabyte-gaming-oc", resultado.url_produto)

    @patch("scraper._buscar_html")
    def test_retorna_none_quando_nenhum_resultado_e_parecido_o_suficiente(self, mock_buscar_html):
        mock_buscar_html.return_value = _ler_fixture("terabyte_busca_rtx4060.html")

        resultado = buscar_preco_terabyte("Teclado Mecânico ABNT2 RGB")

        self.assertIsNone(resultado)

    @patch("scraper._buscar_html")
    def test_retorna_none_quando_busca_nao_encontra_cards(self, mock_buscar_html):
        mock_buscar_html.return_value = "<html><body>0 resultados</body></html>"

        resultado = buscar_preco_terabyte("Item qualquer")

        self.assertIsNone(resultado)

    @patch("scraper.scraper_client.get")
    def test_propaga_erro_de_rede_como_scraping_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("timeout")

        with self.assertRaises(ScrapingError):
            buscar_preco_terabyte("RTX 4060")


if __name__ == "__main__":
    unittest.main()