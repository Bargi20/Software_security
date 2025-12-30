#!/bin/bash

# Script per fermare i container Docker della blockchain Besu

echo "🛑 Arresto dei container Docker..."
echo "================================"

# Naviga alla directory del progetto (dove si trova docker-compose.yml)
cd "$(dirname "$0")"

# Ferma e rimuove i container
docker-compose down -v

echo ""
echo "✅ Container fermati con successo!"
echo ""
echo "💡 Per riavviare i container: ./start.sh"
echo ""
