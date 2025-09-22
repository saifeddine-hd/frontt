# Styles Directory

Ce dossier contient les styles personnalisés et les configurations CSS pour l'application SecretHawk.

## Structure

- `index.css` - Styles principaux avec Tailwind CSS et composants personnalisés
- `components/` - Styles spécifiques aux composants (si nécessaire)
- `themes/` - Thèmes personnalisés (mode sombre, etc.)

## Utilisation

Les styles sont organisés en couches Tailwind :
- `@layer base` - Styles de base et reset
- `@layer components` - Composants réutilisables
- `@layer utilities` - Utilitaires personnalisés

## Variables CSS

Les variables CSS personnalisées sont définies dans `:root` pour une maintenance facile des couleurs et espacements.