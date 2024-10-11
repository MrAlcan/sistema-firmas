# import os

# folder_path = 'runs/detect'

# # Verificar si la carpeta existe
# if not os.path.exists(folder_path):
#     return '<p>Error: La carpeta runs/detect no existe.</p>'

# # Obtener las subcarpetas
# subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]

# # Verificar si hay subcarpetas
# if not subfolders:
#     return '<p>Error: No se encontraron subcarpetas en runs/detect.</p>'

# # Encontrar la subcarpeta más reciente
# latest_subfolder = max(subfolders, key=lambda x: os.path.getctime(os.path.join(folder_path, x)))
