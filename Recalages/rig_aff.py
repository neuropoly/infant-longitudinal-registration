# Importation des bibliothèques nécessaires
import os           # Pour manipuler les chemins et dossiers
import subprocess   # Pour exécuter les commandes système
import glob         # Pour rechercher des fichiers correspondant à un motif
import shutil       # Pour copier les fichiers (ex: image fixe)

# Sujet à traiter
SUB = "sub-879509"

# Répertoires d'entrée (images originales) et de sortie (images recalées)
INPUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/{SUB}"
OUTPUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_alignees/{SUB}"

# Dossier de sortie pour les recalages et champs de déformation
OUTPUT_SUB_DIR = os.path.join(OUTPUT_BASE, "recalage_dispfield")
os.makedirs(OUTPUT_SUB_DIR, exist_ok=True)  # Création du dossier s'il n'existe pas

# Définition des paires temporelles à recaler (mobile → fixe)
PAIRS = [
    ("ses-6mo", "ses-3mo"),
    ("ses-10mo", "ses-3mo"),
    ("ses-10mo", "ses-6mo")
]

# Boucle sur chaque paire d’images
for ses_mov, ses_fix in PAIRS:  # Sens du recalage
    print(f"\n=== Recalage T1-T1 : {ses_mov} → {ses_fix} ===")

    # Répertoires contenant les fichiers .nii.gz pour chaque session
    mov_dir = os.path.join(INPUT_BASE, ses_mov, "anat")
    fix_dir = os.path.join(INPUT_BASE, ses_fix, "anat")

    # Recherche des fichiers IRM T1 (images mobile et fixe)
    t1_mov = sorted(glob.glob(os.path.join(mov_dir, "*T1w*.nii*")))
    t1_fix = sorted(glob.glob(os.path.join(fix_dir, "*T1w*.nii*")))

    # Vérifie que les deux images existent
    if not t1_mov or not t1_fix:
        print(f" Image manquante pour {ses_mov} ou {ses_fix}")
        continue

    # Sélectionne le premier fichier T1w trouvé
    moving_path = t1_mov[0]
    fixed_path = t1_fix[0]

    # Dossier de sortie pour cette paire
    output_dir = os.path.join(OUTPUT_SUB_DIR, f"{ses_mov}_to_{ses_fix}")
    os.makedirs(output_dir, exist_ok=True)

    # Préfixe pour tous les fichiers de sortie
    output_prefix = os.path.join(output_dir, f"{SUB}_{ses_mov}_to_{ses_fix}_T1-T1_reg")

    # Copie l'image fixe pour traçabilité
    fixed_copy_path = os.path.join(output_dir, f"{SUB}_{ses_fix}_T1w_fixed.nii.gz")
    shutil.copy(fixed_path, fixed_copy_path)

    # Recalage rigide suivi d’un recalage affine avec ANTs (deux étapes enchaînées)
    command = [
        "antsRegistration", "-d", "3",  # 3D
        "-m", f"MI[{fixed_path},{moving_path},1,32]",  # Similarité MI pour rigid
        "-t", "Rigid[0.1]",  # Recalage rigide
        "-c", "[1000x500x250x100,1e-6,10]",  # Critère d’arrêt rigid
        "-s", "4x2x1x0vox",  # Smoothing rigid
        "-f", "8x4x2x1",     # Downsampling rigid

        "-m", f"MI[{fixed_path},{moving_path},1,32]",  # Similarité MI pour affine
        "-t", "Affine[0.1]",  # Recalage affine
        "-c", "[1000x500x250x100,1e-6,10]",  # Critère d’arrêt affine
        "-s", "4x2x1x0vox",  # Smoothing affine
        "-f", "8x4x2x1",     # Downsampling affine

        "-o", f"[{output_prefix}_,{output_prefix}_Warped.nii.gz,{output_prefix}_InverseWarped.nii.gz]"
    ]

    # Exécution de la commande de recalage
    try:
        subprocess.run(command, check=True)
        print(f"Recalage réussi : {output_prefix}_0GenericAffine.mat")
    except subprocess.CalledProcessError:
        print(f"Échec recalage {ses_mov} → {ses_fix}")
        continue

    # Fichiers requis pour générer le champ de déplacement
    affine_mat = f"{output_prefix}_0GenericAffine.mat"  # Transformation affine calculée
    disp_field = f"{output_prefix}_disp.nii.gz"          # Champ de déplacement à générer

    print("Génération displacement field via antsApplyTransforms")

    # Génère un champ de déplacement équivalent à la transformation affine
    subprocess.run([
        "antsApplyTransforms", "-d", "3",       # 3D
        "-r", fixed_path,                       # Image de référence (fixe)
        "-t", affine_mat,                       # Transformation à appliquer
        "-o", f"[{disp_field},1]"               # Sortie : displacement field (1 → sortie vectorielle)
    ], check=True)

    print(f"Displacement field généré : {disp_field}")

print("\n=== Pipeline terminé ===")
