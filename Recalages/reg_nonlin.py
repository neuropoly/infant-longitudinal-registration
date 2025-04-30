# Importation des bibliothèques nécessaires
import os           # Pour manipuler les chemins de fichiers
import subprocess   # Pour exécuter des commandes système (ex: antsRegistration)
import shutil       # Pour copier des fichiers (ex: image fixe)

# Sujet à traiter
SUB = "sub-879509"

# Répertoire contenant les images préalablement alignées rigide/affine
BASE_DIR = f"/home/ge.polymtl.ca/calore/projet3/images_alignees/{SUB}"

# Répertoire où sauvegarder les résultats du recalage non-linéaire SyN
OUT_DIR = f"/home/ge.polymtl.ca/calore/projet3/images_non_lineairees/{SUB}"

# Liste des paires à recalculer (image mobile → image fixe)
PAIRS = [
    ("ses-3mo", "ses-6mo"),   # Recaler 6 mois vers 3 mois
    ("ses-3mo", "ses-10mo"),  # Recaler 10 mois vers 3 mois
    ("ses-6mo", "ses-10mo"),  # Recaler 10 mois vers 6 mois
]

print("\nDébut recalage non-linéaire SyN")

# Boucle principale sur toutes les paires
for SES_REF, SES_MOV in PAIRS:  # Sens du recalage
    print("==========================================")
    print(f"Recalage non-linéaire : {SES_REF} ← {SES_MOV}")
    print("==========================================")

    # Dossier contenant l'image alignée rigide/affine
    IN_DIR = os.path.join(BASE_DIR, f"{SES_MOV}_to_{SES_REF}")

    # Chemins vers l'image mobile (déjà rigide/affine) et l'image fixe
    MOVING = os.path.join(IN_DIR, f"{SUB}_{SES_MOV}_to_{SES_REF}_T1-T1_reg_Warped.nii.gz")
    FIXED = os.path.join(IN_DIR, f"{SUB}_{SES_REF}_T1w_fixed.nii.gz")

    # Dossier de sortie pour cette paire
    OUT_SUBDIR = os.path.join(OUT_DIR, f"{SES_MOV}_to_{SES_REF}")
    os.makedirs(OUT_SUBDIR, exist_ok=True)

    # Préfixe pour les fichiers produits par ANTs
    OUT_PREFIX = os.path.join(OUT_SUBDIR, f"{SUB}_{SES_MOV}_to_{SES_REF}_T1-T1_syn")

    # Copie l'image fixe pour référence dans le dossier de sortie
    shutil.copy(FIXED, os.path.join(OUT_SUBDIR, f"{SUB}_{SES_REF}_T1w_fixed.nii.gz"))

    # Vérifie que les fichiers mobile et fixe existent avant de lancer le recalage
    if os.path.isfile(MOVING) and os.path.isfile(FIXED):
        print("Lancement antsRegistration...")

        # Commande pour effectuer uniquement le recalage non-linéaire SyN
        cmd = [
            "antsRegistration", "-d", "3",  # Travail en 3D
            "-m", f"Mattes[{FIXED},{MOVING},1,32]",  # Métrique Mattes (adaptée si intensité similaire)
            "-t", "SyN[0.02,1,0]",           # Transformation SyN (non-linéaire), avec paramètres (gradient step, updateFieldSigma, totalFieldSigma)
            "-c", "[70x50x20x10,1e-6,10]",   # Critères d'arrêt (niveaux d'itération et tolérances)
            "-s", "3x2x1x0vox",              # Lissage gaussien multirésolution
            "-f", "6x4x2x1",                 # Facteurs de sous-échantillonnage multirésolution
            "--interpolation", "Linear",     # Interpolation linéaire
            "--use-histogram-matching", "0", # Pas de matching d'histogramme (important pour T1 → T1)
            "-o", f"{OUT_PREFIX}_"           # Fichiers de sortie : warp et transformations
        ]
        
        # Exécution de la commande de recalage SyN
        try:
            subprocess.run(cmd, check=True)
            print("Recalage terminé.")
            print(f"Outputs générés dans : {OUT_SUBDIR}\n")
        except subprocess.CalledProcessError as e:
            print("ERREUR lors du recalage antsRegistration")
            print(e, "\n")
    else:
        print("Fichier manquant → recalage ignoré.\n")

print("Tous les recalages non-linéaires SyN sont terminés.")
