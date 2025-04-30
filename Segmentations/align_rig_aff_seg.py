# Importation des modules nécessaires
import os               # Pour gérer les chemins de fichiers et les répertoires
import subprocess       # Pour exécuter des commandes système (ex: antsApplyTransforms)
import nibabel as nib    # Pour manipuler les fichiers d'imagerie médicale au format .nii/.nii.gz
import numpy as np       # Pour traiter les matrices d'images (conversion de type)

# Sujet à traiter (identifiant du sujet)
SUB = "sub-879509"

# Répertoires de travail
SRC_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_segmentees/{SUB}"            # Répertoire contenant les segmentations SynthSeg
FIX_IMG_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_alignees/{SUB}"           # Répertoire contenant les images fixes après recalage rigide/affine
OUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_segmentees_alignees/{SUB}"    # Répertoire de sortie pour les segmentations alignées
TRANSFORM_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_alignees/{SUB}/recalage_dispfield" # Répertoire contenant les matrices de transformation rigide/affine

# Liste des paires temporelles à traiter (mobile → fixe)
PAIRS = [
    ("ses-6mo", "ses-3mo"),
    ("ses-10mo", "ses-3mo"),
    ("ses-10mo", "ses-6mo"),
]

print("Alignement des segmentations SynthSeg (resampled → ref, avec conversion en uint8)\n")

# Boucle principale sur chaque paire
for ses_mov, ses_fix in PAIRS:
    print(f" {ses_mov} → {ses_fix}")

    # Chemin vers la segmentation resamplée (mobile)
    resampled_seg = f"{SRC_BASE}/{ses_mov}/anat/seg_{SUB}_{ses_mov}.nii.gz"

    # Chemin vers l'image fixe de référence
    ref_img = f"{FIX_IMG_BASE}/{ses_mov}_to_{ses_fix}/{SUB}_{ses_fix}_T1w_fixed.nii.gz"

    # Chemin vers la matrice de transformation rigide/affine trouvée avec antsRegistration
    mat_path = f"{TRANSFORM_BASE}/{ses_mov}_to_{ses_fix}/{SUB}_{ses_mov}_to_{ses_fix}_T1-T1_reg_0GenericAffine.mat"
    transform_arg = f"[{mat_path},0]"  # Syntaxe exigée par antsApplyTransforms

    # Dossier de sortie pour cette paire
    out_dir = f"{OUT_BASE}/{ses_mov}_to_{ses_fix}"
    os.makedirs(out_dir, exist_ok=True)

    # Chemin final pour sauvegarder la segmentation alignée
    out_seg = f"{out_dir}/seg_{SUB}_{ses_mov}_to_{ses_fix}_aligned.nii.gz"

    # Affichage des chemins utilisés
    print(f"  MOV_SEG   : {resampled_seg}")
    print(f"  REF_IMG   : {ref_img}")
    print(f"  TRANSFORM : {transform_arg}")

    # Vérification de l'existence des fichiers requis
    if not all(os.path.isfile(p) for p in [resampled_seg, ref_img, mat_path]):
        print(" Fichier manquant → on saute.\n")
        continue

    # Conversion de la segmentation en uint8 (entiers entre 0 et 255) pour éviter des problèmes d'interpolation
    print(" Conversion en uint8...")
    img_nii = nib.load(resampled_seg)                          # Chargement de l'image
    data = np.round(img_nii.get_fdata()).astype(np.uint8)       # Conversion des données en entier uint8
    tmp_uint8_seg = os.path.join(out_dir, "tmp_uint8_seg.nii.gz")  # Chemin temporaire pour sauvegarder
    nib.Nifti1Image(data, img_nii.affine, img_nii.header).to_filename(tmp_uint8_seg) # Sauvegarde du fichier temporaire

    # Application de la transformation rigide/affine à la segmentation
    print(" Application transformation rigide/affine...")
    try:
        subprocess.run([
            "antsApplyTransforms", "-d", "3",              # 3D
            "-i", tmp_uint8_seg,                           # Image mobile : la segmentation convertie uint8
            "-r", ref_img,                                 # Image fixe : référence pour alignement spatial
            "-t", transform_arg,                           # Transformation rigide/affine
            "-n", "NearestNeighbor",                       # Interpolation par plus proche voisin (important pour préserver les labels)
            "-o", out_seg                                  # Fichier de sortie
        ], check=True)

        print(f" Sauvegardé : {out_seg}\n")

    except subprocess.CalledProcessError as e:
        # Gestion d'erreur si antsApplyTransforms échoue
        print(" ÉCHEC de antsApplyTransforms")
        print(e, "\n")

# Fin de la boucle sur toutes les paires
print("Tous les recalages sont terminés.")
