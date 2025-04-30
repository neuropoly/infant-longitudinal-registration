# Importation des modules nécessaires
import os           # Pour gérer les chemins de fichiers et répertoires
import subprocess   # Pour exécuter des commandes système (ex: antsApplyTransforms)

# Sujet à traiter
SUB = "sub-879509"

# Répertoire où se trouvent les images recalées rigide/affine
BASE_DIR = f"/mnt/c/Users/camil/Downloads/p3/images_alignees/{SUB}"

# Répertoire où seront enregistrées les images transformées après recalage non-linéaire
OUT_DIR = f"/mnt/c/Users/camil/Downloads/p3/images_non_lineairees/{SUB}"

# Liste des paires longitudinales (mobile → fixe)
PAIRS = [
    ("ses-3mo", "ses-6mo"),   # Image mobile 6 mois → image fixe 3 mois
    ("ses-3mo", "ses-10mo"),  # Image mobile 10 mois → image fixe 3 mois
    ("ses-6mo", "ses-10mo"),  # Image mobile 10 mois → image fixe 6 mois
]

print("\nDébut application des transformations antsApplyTransforms")

# Boucle principale sur chaque paire de sessions
for SES_REF, SES_MOV in PAIRS:
    print("==========================================")
    print(f"Transformation : {SES_MOV} → {SES_REF}")
    print("==========================================")

    # Définition du dossier contenant les résultats rigide/affine de cette paire
    IN_DIR = os.path.join(BASE_DIR, f"{SES_MOV}_to_{SES_REF}")

    # Chemin vers l'image mobile (déjà alignée rigide/affine)
    MOVING = os.path.join(IN_DIR, f"{SUB}_{SES_MOV}_to_{SES_REF}_T1-T1_reg_Warped.nii.gz")

    # Chemin vers l'image fixe (référence)
    FIXED = os.path.join(IN_DIR, f"{SUB}_{SES_REF}_T1w_fixed.nii.gz")

    # Dossier et préfixe de sortie pour la transformation non-linéaire
    OUT_SUBDIR = os.path.join(OUT_DIR, f"{SES_MOV}_to_{SES_REF}")
    OUT_PREFIX = os.path.join(OUT_SUBDIR, f"{SUB}_{SES_MOV}_to_{SES_REF}_T1-T1_syn")

    # Chemin vers le fichier de champ de déformation produit par antsRegistration (SyN)
    WARP_FILE = f"{OUT_PREFIX}_0Warp.nii.gz"

    # Chemin de sortie pour l'image finale transformée
    OUTPUT_WARPED = f"{OUT_PREFIX}_Warped.nii.gz"

    # Vérification de l'existence des fichiers nécessaires
    missing = []
    for file in [MOVING, FIXED, WARP_FILE]:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        # Si des fichiers sont manquants, afficher un message et passer à la paire suivante
        print("Fichiers manquants → Transformation sautée")
        for m in missing:
            print(f"  - {m}")
        print()
        continue

    print("Application de la déformation...")

    # Application du champ de déformation avec antsApplyTransforms
    try:
        subprocess.run([
            "antsApplyTransforms", "-d", "3",    # Spécifie 3D
            "-i", MOVING,                        # Image mobile (input)
            "-r", FIXED,                         # Image fixe (référence spatiale)
            "-t", WARP_FILE,                     # Champ de déformation à appliquer
            "-o", OUTPUT_WARPED,                 # Image de sortie
            "-n", "Linear"                       # Interpolation linéaire
        ], check=True)

        print(f"Image transformée générée : {OUTPUT_WARPED}\n")

    except subprocess.CalledProcessError as e:
        # Gestion des erreurs d'exécution
        print("ERREUR antsApplyTransforms")
        print(e, "\n")

# Message de fin une fois toutes les paires traitées
print("Toutes les transformations ont été appliquées.")
