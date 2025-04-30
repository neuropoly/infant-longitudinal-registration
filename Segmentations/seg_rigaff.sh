#!/bin/bash
# ===========================================================================
# Segmentation automatique des images réalignées (rigide et affine) avec SynthSeg
# Ce script parcourt toutes les images *_Warped.nii.gz présentes dans BASE_DIR,
# applique SynthSeg pour produire la segmentation, le volume CSV et le QC CSV,
# et enregistre les résultats dans le répertoire correspondant.
# ===========================================================================

# Sujet à traiter
SUB=sub-879509

# Répertoire contenant les images réalignées (résultat d'un recalage rigide/affine)
BASE_DIR="/home/ge.polymtl.ca/calore/projet3/images_alignees/${SUB}"

# Répertoire où seront enregistrées les segmentations SynthSeg
OUT_BASE="/home/ge.polymtl.ca/calore/projet3/images_alignees_segmentees/${SUB}"

echo " Recherche dans : $BASE_DIR"

# Recherche récursive de toutes les images terminant par *_Warped.nii.gz
find "$BASE_DIR" -type f -name "*_Warped.nii.gz" | while read img; do
    echo " Segmentation SynthSeg pour : $img"

    # Extraction du chemin relatif par rapport à BASE_DIR
    relative_path="${img#$BASE_DIR/}"

    # Sous-dossier correspondant (ex: ses-6mo_to_ses-3mo)
    subdir=$(dirname "$relative_path")

    # Nom de base du fichier sans suffixe (_Warped.nii.gz)
    base=$(basename "$img" "_Warped.nii.gz")

    # Création du dossier de sortie correspondant
    out_dir="${OUT_BASE}/${subdir}"
    mkdir -p "$out_dir"

    # Définition des chemins de sortie
    output="${out_dir}/seg_${base}.nii.gz"           # Fichier de segmentation produit
    volume_csv="${out_dir}/volumes_${base}.csv"      # Fichier des volumes extraits
    qc_csv="${out_dir}/qc_${base}.csv"                # Fichier de qualité de segmentation

    # Exécution de SynthSeg sur l'image trouvée
    mri_synthseg \
        --i "$img" \              # Image d'entrée
        --o "$output" \           # Chemin de la segmentation de sortie
        --vol "$volume_csv" \     # Chemin du CSV des volumes
        --qc "$qc_csv" \          # Chemin du CSV d'évaluation de la qualité (QC)
        --cpu                     # Utilisation du CPU pour exécution

    echo " Sauvegardé : $output"
done

# Message final
echo " Toutes les segmentations sont terminées."
