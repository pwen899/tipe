#!/bin/bash

# Définition du chemin du script Python
SCRIPT_PATH="/run/media/pierre/Shared/mpii/tipe/repo/manage_site.py"

# Vérification de l'existence du script
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erreur : Le fichier $SCRIPT_PATH n'existe pas."
    exit 1
fi

# Exécution du script Python avec l'interpréteur par défaut
echo "Exécution du script Python..."
python3 "$SCRIPT_PATH"

# Vérification du statut de l'exécution
if [ $? -eq 0 ]; then
    echo "Le script a été exécuté avec succès !"
else
    echo "Erreur lors de l'exécution du script."
fi
