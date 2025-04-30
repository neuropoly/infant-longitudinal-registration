#!/bin/bash
# ===========================================================================
# Segmentation des images alignées rigide avec SynthSeg
# Ce script parcourt toutes les images recalées rigide (_rigid_Warped.nii.gz)
# et applique SynthSeg pour produire la segmentation, les volumes et le QC
# ===========================================================================

# Sujet à traiter
SUB=sub-879509

# Répertoire contenant les images réalignées (rigide)
BASE_DIR="/home/ge.polymtl.ca/calore/projet3/images_alignees/${SUB}"

# Répertoire où sauvegarder les segmentations SynthSeg correspondantes
OUT_BASE="/home/ge.polymtl.ca/calore/projet3/images_rig_segmentees/${SUB}"

echo " Recherche dans : $BASE_DIR"

# Boucle sur toutes les images *_rigid_Warped.nii.gz trouvées récursivement
find "$BASE_DIR" -type f -name "*rigid_Warped.nii.gz" | while read img; do
    echo " Segmentation SynthSeg pour : $img"

    # Extraction du chemin relatif par rapport à BASE_DIR
    relative_path="${img#$BASE_DIR/}"

    # Sous-dossier de l'image (ex: ses-6mo_to_ses-3mo)
    subdir=$(dirname "$relative_path")

    # Nom de base du fichier (sans suffixe _rigid_Warped.nii.gz)
    base=$(basename "$img" "rigid_Warped.nii.gz")

    # Création du dossier de sortie
    out_dir="${OUT_BASE}/${subdir}"
    mkdir -p "$out_dir"

    # Définition des chemins de sortie
    output="${out_dir}/seg_rig_${base}.nii.gz"             # Segmentation finale
    volume_csv="${out_dir}/volumes_rig_${base}.csv"        # Volumes segmentés
    qc_csv="${out_dir}/qc_rig_${base}.csv"                 # Fichier de qualité (QC)

    # Exécution de SynthSeg
    mri_synthseg \
        --i "$img" \              # Image d’entrée
        --o "$output" \           # Fichier de segmentation en sortie
        --vol "$volume_csv" \     # Fichier CSV des volumes
        --qc "$qc_csv" \          # Fichier CSV d'évaluation de la qualité
        --cpu                     # Exécution sur CPU

    echo " Sauvegardé : $output"
done

echo " Toutes les segmentations sont terminées."
