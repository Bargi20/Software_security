#!/bin/bash

# Script per avviare i container Docker della blockchain Besu

echo "🚀 Avvio dei container Docker..."
echo "================================"

# Naviga alla directory del progetto (dove si trova docker-compose.yml)
cd "$(dirname "$0")"
docker-compose build

# Avvia i container in modalità detached
docker-compose up -d

# Attendi qualche secondo per permettere ai container di avviarsi
echo ""
echo "⏳ Attendo l'avvio dei container..."
sleep 5

# Mostra lo stato dei container
echo ""
echo "📊 Stato dei container:"
docker-compose ps

echo ""
echo "✅ Container avviati!"
echo ""
echo "💡 Informazioni utili:"
echo "   - Nodo Besu (validator1): http://localhost:8545"
echo "   - Per vedere i log: docker-compose logs -f"
echo "   - Per fermare i container: ./stop.sh"
echo ""
