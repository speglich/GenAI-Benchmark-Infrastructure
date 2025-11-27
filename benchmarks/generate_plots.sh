#!/bin/bash

SOURCE_DIR="/home/opc/benchmarks"
DEST_DIR="/home/opc/benchmarks/results"

mkdir -p "$DEST_DIR"

# Percorre todas as pastas do Benchmark
find "$SOURCE_DIR" -type d | while read -r dir; do
    meta="$dir/experiment_metadata.json"

    # Só continua se metadata existir
    if [[ -f "$meta" ]]; then
        echo "Processando: $dir"

        # Extrai traffic_scenario[0]
        traffic=$(jq -r '.traffic_scenario[0]' "$meta")

        # Extrai api_backend
        backend=$(jq -r '.api_backend' "$meta")

        # Monta o nome da pasta
        folder_name="${backend}_${traffic}"

        # Remove caracteres problemáticos para nomes de pastas
        sanitized=$(echo "$folder_name" | sed 's#[()/ ]##g')

        # Cria o diretório final
        mkdir -p "$DEST_DIR/$sanitized"

        # Copia todos os N*.json da pasta
        find "$dir" -maxdepth 1 -type f -name "N*.json" -exec cp {} "$DEST_DIR/$sanitized/" \;

    fi
done

/home/opc/.venv/bin/python /home/opc/benchmarks/plot.py