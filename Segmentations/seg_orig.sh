#!/bin/bash
# ========================================================
# Script Bash pour segmenter les images T1w originales
# non alignées avec SynthSeg (avec options volumes, QC et resampling)
# ========================================================

# Sujet à traiter
SUB=sub-879509

# Répertoire source contenant les images corrigées du biais (N4) après skull stripping
SRC_BASE="/home/ge.polymtl.ca/calore/hc-bcp/derivatives/n4_bias_correction/${SUB}"

# Répertoire de destination où seront stockées les segmentations SynthSeg
DST_BASE="/home/ge.polymtl.ca/calore/projet3/images_segmentees/${SUB}"

# Boucle sur les différentes sessions (âge : 3 mois, 6 mois, 10 mois)
for SES in ses-3mo ses-6mo ses-10mo; do

  # Localisation de l'image source à segmenter (on prend la première occurrence trouvée)
  SRC_IMG=$(ls ${SRC_BASE}/${SES}/anat/${SUB}_${SES}_run-*_T1w_stripped_n4.nii.gz | head -n 1)

  # Définition du répertoire de sortie pour la session
  DST_DIR="${DST_BASE}/${SES}/anat"

  # Chemins pour les fichiers de sortie
  SEG_OUT="${DST_DIR}/seg_${SUB}_${SES}.nii.gz"           # Segmentation finale
  RESAMPLED_OUT="${DST_DIR}/resampled_${SUB}_${SES}.nii.gz" # Image resamplée
  VOL_CSV="${DST_DIR}/volumes_${SUB}_${SES}.csv"          # Fichier CSV des volumes
  QC_CSV="${DST_DIR}/qc_${SUB}_${SES}.csv"                # Fichier CSV de qualité (QC)

  # Vérification que l'image source existe avant de lancer la segmentation
  if [ -f "$SRC_IMG" ]; then
    mkdir -p "$DST_DIR"   # Crée le dossier de destination si nécessaire
    echo " Segmentation SynthSeg : $SRC_IMG"

    # Appel à mri_synthseg pour segmenter l'image
    mri_synthseg \
      --i "$SRC_IMG" \          # Input : image NIfTI à segmenter
      --o "$SEG_OUT" \          # Output : fichier de segmentation
      --resample "$RESAMPLED_OUT" \ # Image resamplée à résolution standardisée
      --vol "$VOL_CSV" \        # Calcul et export des volumes segmentés
      --qc "$QC_CSV" \          # Calcul et export des métriques de qualité de segmentation
      --cpu                    # Force l'exécution sur CPU (pas de GPU)

    echo "Sauvegardé : $SEG_OUT"

  else
    # Si l'image source n'est pas trouvée, afficher un message d'erreur
    echo "Image non trouvée : $SRC_IMG"
  fi

done

# Message de fin après traitement de toutes les sessions
echo " Toutes les segmentations sont terminées."
