import os
import pygame

def import_folder(path):
    surface_list = []

    if not os.path.exists(path):
        return surface_list

    for file_name in sorted(os.listdir(path)):
        full_path = os.path.join(path, file_name)
        if os.path.isfile(full_path) and file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                image_surf = pygame.image.load(full_path).convert_alpha()
                surface_list.append(image_surf)
            except Exception as e:
                print(f"Failed to load image: {full_path} → {e}")

    return surface_list
