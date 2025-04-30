# Importation des bibliothèques nécessaires
import os           # Pour la gestion des chemins de fichiers et répertoires
import subprocess   # Pour exécuter des commandes système (ex: antsApplyTransforms)
import shutil       # Pour copier des fichiers (ex: sauvegarde avant recalage)

# ================================================
# Alignement non-linéaire (SyN) des segmentations
# sur les images déjà alignées rigide+affine
# ================================================

# Sujet à traiter
SUB = "sub-879509"

# Définition des répertoires
SRC_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_segmentees_alignees/{SUB}"    # Segmentations déjà alignées rigide/affine
WARP_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_non_lineairees/{SUB}"        # Champs de déformation produits par SyN
REF_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_non_lineairees/{SUB}"         # Images fixes correspondantes (référence spatiale)
OUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/seg_nonlin_appliquees/{SUB}"         # Où enregistrer les segmentations après recalage non-linéaire

# Liste des paires (référence ← mobile)
PAIRS = [
    ("ses-3mo", "ses-6mo"),   # Appliquer la déformation de 6 mois vers 3 mois
    ("ses-3mo", "ses-10mo"),  # Appliquer la déformation de 10 mois vers 3 mois
    ("ses-6mo", "ses-10mo"),  # Appliquer la déformation de 10 mois vers 6 mois
]

# Boucle principale sur chaque paire temporelle
for ses_fix, ses_mov in PAIRS:
    print(f"\n Application champ de déformation : {ses_fix} ← {ses_mov}")

    # Chemin vers le champ de déformation non-linéaire généré par SyN
    warp_field = os.path.join(
        WARP_BASE,
        f"{ses_mov}_to_{ses_fix}",
        f"{SUB}_{ses_mov}_to_{ses_fix}_T1-T1_syn_0Warp.nii.gz"
    )

    # Chemin vers l’image segmentée préalablement alignée rigide/affine
    mov_seg = os.path.join(
        SRC_BASE,
        f"{ses_mov}_to_{ses_fix}",
        f"seg_{SUB}_{ses_mov}_to_{ses_fix}_aligned.nii.gz"
    )

    # Chemin vers l'image de référence (fixe)
    ref_img = os.path.join(
        REF_BASE,
        f"{ses_mov}_to_{ses_fix}",
        f"{SUB}_{ses_fix}_T1w_fixed.nii.gz"
    )

    # Dossier de sortie et chemin du fichier de segmentation non-linéaire transformée
    out_dir = os.path.join(OUT_BASE, f"{ses_mov}_to_{ses_fix}")
    os.makedirs(out_dir, exist_ok=True)  # Création du dossier si nécessaire
    out_seg = os.path.join(out_dir, f"seg_{SUB}_{ses_mov}_to_{ses_fix}_nonlin.nii.gz")

    # Affiche les chemins utilisés pour vérification
    print(f"   MOV_SEG  : {mov_seg}")
    print(f"   WARP     : {warp_field}")
    print(f"   REF_IMG  : {ref_img}")
    print(f"   OUT_SEG  : {out_seg}")

    # Vérifie l'existence de tous les fichiers nécessaires avant de continuer
    if not all(os.path.isfile(p) for p in [warp_field, mov_seg, ref_img]):
        print(" Fichier manquant → on saute.")
        continue

    # Sauvegarde des fichiers d'entrée dans le dossier de sortie (copie de sécurité)
    shutil.copy(mov_seg, os.path.join(out_dir, f"input_{os.path.basename(mov_seg)}"))
    shutil.copy(warp_field, os.path.join(out_dir, f"{os.path.basename(warp_field)}"))

    # Application du champ de déformation non-linéaire avec antsApplyTransforms
    try:
        subprocess.run([
            "antsApplyTransforms", "-d", "3",         # 3D
            "-i", mov_seg,                            # Image mobile : segmentation alignée rigide/affine
            "-r", ref_img,                            # Image fixe : référence
            "-t", warp_field,                         # Transformation non-linéaire (champ SyN)
            "-n", "NearestNeighbor",                  # Interpolation par plus proche voisin (important pour segmentations)
            "-o", out_seg                             # Fichier de sortie
        ], check=True)

        print(" Transformation appliquée.")
    except subprocess.CalledProcessError as e:
        # Gestion des erreurs si antsApplyTransforms échoue
        print(" Échec de transformation")
        print(e)

# Message final après traitement de toutes les paires
print("\n Toutes les transformations ont été appliquées.")
