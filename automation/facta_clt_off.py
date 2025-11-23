#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from datetime import datetime
import time

def configurar_logger(log_dir):
    """
    Cria o arquivo de log com timestamp e configura o logger.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(log_dir, f"facta_{timestamp}.log")

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    return log_path


def processar_planilha(input_path):
    """
    Simulação do processamento real — aqui você coloca a lógica da automação.
    """
    logging.info("Iniciando processamento da planilha: %s", input_path)

    # Simulando 5 etapas como você pediu
    for i in range(1, 6):
        logging.info(f"Executando etapa {i}/5 ...")
        time.sleep(1)   # simula processamento

    logging.info("Processamento concluído com sucesso para: %s", input_path)


def main():
    parser = argparse.ArgumentParser(description="Automação FACTA CLT OFF")
    parser.add_argument("--input", required=True, help="Arquivo enviado pelo usuário")
    parser.add_argument("--log_dir", required=True, help="Diretório de logs")

    args = parser.parse_args()

    # Configurando logger
    log_path = configurar_logger(args.log_dir)
    logging.info("Script FACTA CLT OFF iniciado.")
    logging.info("Parâmetros recebidos: input='%s', log_dir='%s'", args.input, args.log_dir)

    # Validação simples
    if not os.path.exists(args.input):
        logging.error("Arquivo de entrada não encontrado.")
        logging.info("Script FACTA CLT OFF finalizado com erro.")
        sys.exit(1)

    # Processamento
    try:
        processar_planilha(args.input)
        logging.info("Script FACTA CLT OFF finalizado sem erro. Log em: %s", log_path)
    except Exception as e:
        logging.error(f"Erro no processamento: {e}")
        logging.info("Script FACTA CLT OFF finalizado com erro.")
        sys.exit(1)


if __name__ == "__main__":
    main()
