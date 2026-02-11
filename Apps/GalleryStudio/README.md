# CasaOS App Store Submission

This directory contains the files needed to submit Gallery Studio to the official CasaOS App Store.

## Files

- `docker-compose.yml` - The compose file for the App Store (uses versioned images)
- `icon.png` - App icon (512x512)
- `thumbnail.png` - Thumbnail image
- `screenshot-1.png` - Screenshot (add after taking screenshots)

## Submission Process

1. **Wait for v1.0.0 images to build** on GitHub Actions
2. **Test the installation** using the compose file
3. **Fork the CasaOS App Store**: https://github.com/IceWhaleTech/CasaOS-AppStore
4. **Create a new folder**: `Apps/GalleryStudio/`
5. **Copy these files** to that folder
6. **Submit a Pull Request** with your changes

## Notes

- The compose file uses versioned images (`v1.0.0`) instead of `:latest`
- All paths are absolute and use Docker volumes
- The App Store team will review and merge if approved
