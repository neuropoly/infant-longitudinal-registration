#!/bin/bash
# ===========================================================================
# Segmentation automatique des images réalignées non-linéaires (SyN) avec SynthSeg
# Ce script parcourt toutes les images *_syn_Warped.nii.gz dans BASE_DIR,
# applique SynthSeg pour produire la segmentation, les volumes CSV et les QC CSV,
# et sauvegarde les résultats dans un dossier correspondant.
# ===========================================================================

# Sujet à traiter
SUB=sub-879509

# Répertoire contenant les images recalées non-linéairement (SyN)
BASE_DIR="/home/ge.polymtl.ca/calore/projet3/images_non_lineairees/${SUB}"

# Répertoire de sortie pour sauvegarder les segmentations SynthSeg
OUT_BASE="/home/ge.polymtl.ca/calore/projet3/seg_nonlin/${SUB}"

echo "Recherche dans : $BASE_DIR"

# Boucle sur toutes les images trouvées correspondant à *_syn_Warped.nii.gz
find "$BASE_DIR" -type f -name "*_syn_Warped.nii.gz" | while read img; do
    echo "Segmentation SynthSeg pour : $img"

    # Extraction du chemin relatif à partir de BASE_DIR
    relative_path="${img#$BASE_DIR/}"  # Exemple: ses-6mo_to-ses-3mo/nom.nii.gz

    # Extraction du sous-dossier de l'image (ex: ses-6mo_to_ses-3mo)
    subdir=$(dirname "$relative_path")

    # Extraction du nom de base du fichier (sans suffixe _syn_Warped.nii.gz)
    base=$(basename "$img" "_syn_Warped.nii.gz")

    # Création du répertoire de sortie correspondant
    out_dir="${OUT_BASE}/${subdir}"
    mkdir -p "$out_dir"

    # Définition des chemins de sortie
    output="${out_dir}/seg_${base}.nii.gz"       # Fichier de segmentation
    vol_csv="${out_dir}/volumes_${base}.csv"     # Fichier CSV des volumes segmentés
    qc_csv="${out_dir}/qc_${base}.csv"            # Fichier CSV de qualité (QC)

    # Exécution de la segmentation SynthSeg
    mri_synthseg \
        --i "$img" \               # Image d'entrée
        --o "$output" \             # Segmentation en sortie
        --vol "$vol_csv" \          # Volumes en sortie
        --qc "$qc_csv" \            # QC en sortie
        --cpu                      # Utilisation du CPU

    echo "Sauvegardé : $output"
done

# Message final de confirmation
echo "Toutes les segmentations sont terminées."
