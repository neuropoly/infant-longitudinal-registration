# Importation des bibliothèques nécessaires
import os           # Pour la manipulation des chemins de fichiers et la création de dossiers
import subprocess   # Pour exécuter des commandes système (ex : antsRegistration)
import glob         # Pour rechercher des fichiers correspondant à un motif
import shutil       # Pour copier des fichiers (ici, copier l’image fixe)

# Définition du sujet à traiter
SUB = "sub-879509"

# Définition des chemins de base
INPUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/{SUB}"                 # Chemin vers les données d’entrée (IRM)
OUTPUT_BASE = f"/mnt/c/Users/camil/Downloads/p3/images_rigides/{SUB}/" # Chemin vers les résultats de recalage
OUTPUT_SUB_DIR = os.path.join(OUTPUT_BASE, SUB)                      # Sous-dossier spécifique au sujet
os.makedirs(OUTPUT_SUB_DIR, exist_ok=True)                           # Crée le répertoire de sortie s’il n’existe pas

# Définition des paires temporelles à recaler (image mobile → image fixe)
PAIRS = [
    ("ses-6mo", "ses-3mo"),   # Recalage de l’image à 6 mois vers celle à 3 mois
    ("ses-10mo", "ses-3mo"),  # Recalage de 10 mois vers 3 mois
    ("ses-10mo", "ses-6mo")   # Recalage de 10 mois vers 6 mois
]

# Boucle principale : traitement de chaque paire
for ses_mov, ses_fix in PAIRS:  # Sens du recalage
    print(f" Recalage rigide T1-T1 : {ses_mov} → {ses_fix}")

    # Chemins vers les dossiers contenant les images T1w
    mov_dir = os.path.join(INPUT_BASE, ses_mov, "anat")  # Dossier image mobile
    fix_dir = os.path.join(INPUT_BASE, ses_fix, "anat")  # Dossier image fixe

    # Recherche des fichiers IRM T1w (*.nii ou *.nii.gz) dans chaque dossier
    t1_mov = sorted(glob.glob(os.path.join(mov_dir, "*T1w*.nii*")))
    t1_fix = sorted(glob.glob(os.path.join(fix_dir, "*T1w*.nii*")))

    # Vérifie que les deux fichiers existent, sinon passe à la prochaine paire
    if not t1_mov or not t1_fix:
        print(f" Image manquante pour {ses_mov} ou {ses_fix}")
        continue

    # Chemins complets vers les fichiers d’images à utiliser
    moving_path = t1_mov[0]
    fixed_path = t1_fix[0]

    # Crée un dossier de sortie pour cette paire temporelle
    output_dir = os.path.join(OUTPUT_SUB_DIR, f"{ses_mov}_to_{ses_fix}")
    os.makedirs(output_dir, exist_ok=True)

    # Préfixe utilisé pour tous les fichiers produits par ANTs
    output_prefix = os.path.join(output_dir, f"{SUB}_{ses_mov}_to_{ses_fix}_T1-T1_rigid")

    # Copie l’image fixe dans le dossier de sortie (utile pour visualiser ou pour les étapes ultérieures)
    fixed_copy_path = os.path.join(output_dir, f"{SUB}_{ses_fix}_T1w_fixed.nii.gz")
    shutil.copy(fixed_path, fixed_copy_path)

    # Préparation de la commande ANTs pour effectuer un recalage rigide
    command = [
        "antsRegistration", "-d", "3",  # Image 3D
        "-m", f"MI[{fixed_path},{moving_path},1,32]",  # Utilisation de l'information mutuelle (MI) comme métrique de similarité
        "-t", "Rigid[0.1]",  # Transformation rigide (rotation + translation), avec step size 0.1
        "-c", "[1000x500x250x100,1e-6,10]",  # Critère d’arrêt : max d’itérations par niveau, seuil de convergence, nb d’itérations consécutives
        "-s", "4x2x1x0vox",  # Lissage gaussien à chaque niveau (multi-échelle)
        "-f", "8x4x2x1",     # Facteurs de downsampling à chaque niveau
        "-o", f"[{output_prefix}_,{output_prefix}_Warped.nii.gz,{output_prefix}_InverseWarped.nii.gz]"  # Fichiers de sortie
    ]

    # Exécution de la commande avec gestion des erreurs
    try:
        subprocess.run(command, check=True)  # Exécute la commande et interrompt si une erreur est rencontrée
        print(f" Recalage rigide réussi : {output_prefix}_0GenericAffine.mat")  # Fichier contenant la matrice de transformation rigide
    except subprocess.CalledProcessError as e:
        print(f" Échec recalage rigide {ses_mov} → {ses_fix}")  # Affiche une erreur si le recalage a échoué
