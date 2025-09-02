# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CasaOS AppStore is a centralized repository for Docker Compose applications designed to run on CasaOS, a personal cloud operating system. The repository contains pre-configured applications that users can easily install and manage through the CasaOS interface.

## Common Development Commands

This repository does not have traditional build/test commands as it primarily serves as a collection of Docker Compose applications. However, for development workflow:

### Adding New Applications
1. Create a new directory under `Apps/` with the application name (lowercase, alphanumeric, hyphens, underscores only)
2. Add at minimum:
   - `docker-compose.yml` - the Docker Compose configuration
   - `icon.png` - 192x192px transparent PNG app icon
   - `screenshot-1.png` - 1280x720px screenshot showing the app running on CasaOS

### Application Validation
- Each application must have a valid `docker-compose.yml` file
- App names in `docker-compose.yml` must match `^[a-z0-9][a-z0-9_-]*$`
- Image tags should be specific (e.g., `:0.1.2`) rather than `:latest`

### Setup Scripts
- `build/scripts/setup/script.d/99-setup-appstore.sh` - Bash script for updating CasaOS default appstore
- `help/action.sh` - Legacy script for processing appfile.json (no longer supported)

## Architecture Overview

### Directory Structure
```
CasaOS-AppStore/
├── Apps/                    # Application directories (one per app)
├── build/                   # Installation scripts
├── psd-source/             # Design templates for app assets
├── category-list.json      # Category definitions
├── featured-apps.json      # Featured app configurations  
├── recommend-list.json     # Recommended app configurations
└── README.md               # Project documentation
```

### Application Structure
Each application in `Apps/` contains:

**Required Files:**
- `docker-compose.yml` - Docker Compose configuration
- `icon.png` - App icon (192x192px, transparent PNG recommended)
- At least one screenshot (`screenshot-1.png`) - 1280x720px

**Optional Files:**
- Additional screenshots (`screenshot-2.png`, `screenshot-3.png`, etc.)
- `thumbnail.png` - Featured app thumbnail (784x442px, transparent PNG)
- `appfile.json` - Legacy format (deprecated since CasaOS v0.4.4)

### Docker Compose Requirements
Applications follow CasaOS-specific conventions:

#### System Variables
Use CasaOS system variables in environment and volumes:
```yaml
environment:
  PGID: $PGID         # Preset Group ID
  PUID: $PUID         # Preset User ID  
  TZ: $TZ             # System timezone
volumes:
  - source: /DATA/AppData/$AppID/config  # App-specific config directory
```

#### CasaOS Extensions (x-casaos)
Metadata is stored under the `x-casaos` extension property:

**Service Level (per service):**
```yaml
services:
  app:
    x-casaos:
      envs:        # Environment variable descriptions
      ports:       # Port descriptions
      volumes:     # Volume descriptions
```

**Compose Level (app-wide):**
```yaml
x-casaos:
  architectures: [amd64, arm64, arm]   # Supported architectures
  main: service_name                    # Main service name
  author: "Your Name"                   # App author
  category: "Category Name"             # Category from category-list.json
  description:                          # Multi-language description
    en_US: "English description"
    zh_CN: "中文描述"
  developer: "Developer Name"            # Original developer
  icon: "https://..."                    # Icon URL
  tagline:                              # Short tagline (multi-language)
    en_US: "English tagline"
  title:                                # App title (multi-language)
    en_US: "App Name"
  port_map: "8080"                      # Web UI port
  index: "/"                            # Index page path
  thumbnail: "https://..."              # Featured thumbnail URL
  tips:                                 # Installation tips
    before_install:
      en_US: "Pre-installation notes"
```

#### Multi-language Description Requirements
**All Docker Compose files must include comprehensive multi-language descriptions** in the `x-casaos` section to ensure global accessibility and user experience. This includes:

**Required Languages:**
- `en_US` - English (US) - Always required as the default language
- Additional languages should be included based on the application's target audience

**Multi-language Fields:**
```yaml
x-casaos:
  description:                          # Detailed app description (multi-language)
    en_US: "Comprehensive English description explaining the application's purpose, features, and benefits..."
    zh_CN: "详细的中文描述，解释应用程序的目的、功能和优势..."
    ja_JP: "日本語の詳細な説明..."
    # Add more languages as needed
  title:                                # App display name (multi-language)
    en_US: "Application Name"
    zh_CN: "应用程序名称"
    ja_JP: "アプリケーション名"
  tagline:                              # Short marketing tagline (multi-language)
    en_US: "Brief English tagline"
    zh_CN: "简短的中文标语"
    ja_JP: "簡潔な日本語のタグライン"
  tips:                                 # Installation and usage tips (multi-language)
    before_install:
      en_US: "English pre-installation notes..."
      zh_CN: "中文安装前说明..."
```

**Service Level Multi-language Descriptions:**
Service-level metadata must also support multiple languages:
```yaml
services:
  app:
    x-casaos:
      envs:
        - container: TZ
          description:
            en_US: TimeZone
            zh_CN: 时区
            ja_JP: タイムゾーン
        - container: PUID
          description:
            en_US: Run application as specified uid.
            zh_CN: 以指定的用户ID运行应用程序。
            ja_JP: 指定されたuidでアプリケーションを実行します。
      ports:
        - container: "8080"
          description:
            en_US: WebUI HTTP Port
            zh_CN: WebUI HTTP端口
            ja_JP: WebUI HTTPポート
      volumes:
        - container: /config
          description:
            en_US: Application configuration directory.
            zh_CN: 应用程序配置目录。
            ja_JP: アプリケーション設定ディレクトリ。
```

**Language Code Standards:**
Use standard language codes: `en_US`, `en_GB`, `zh_CN`, `ja_JP`, `ko_KR`, `fr_FR`, `de_DE`, `es_ES`, `it_IT`, `pt_PT`, `ru_RU`, etc.

**Best Practices:**
1. **Always include `en_US`** as the base language
2. **Add languages relevant to your application's user base**
3. **Provide translations of equivalent quality and detail**
4. **Keep descriptions concise but informative** (similar length across languages)
5. **Use native localization** rather than literal translations
6. **Include installation tips and warnings** in all supported languages

### Special CasaOS Features
- **Dynamic Ports**: Use `${WEBUI_PORT}` for automatic port allocation
- **Environment Variables**: Access user-set environment variables via `/etc/casaos/env`

### Categories and Curation
- `category-list.json` defines available application categories with icons and descriptions
- `featured-apps.json` lists apps featured on the AppStore front page
- `recommend-list.json` contains recommended applications

### Application Testing
All new applications **must** be thoroughly tested on a CasaOS instance before submission. This includes:
- Verifying the app starts successfully
- Testing all major functionality
- Ensuring proper resource allocation
- Validating network connectivity and port exposure

## Contribution Guidelines

### Pull Request Process
1. Fork the repository
2. Create your application following the structure above
3. Test thoroughly on your own CasaOS instance
4. Submit a Pull Request and assign to CasaOS Team or trusted contributor

### Code Quality Standards
- Use specific image tags instead of `:latest`
- Follow Docker Compose best practices
- Include comprehensive descriptions in multiple languages when possible
- Ensure all CasaOS-specific metadata is complete and accurate

### Featured App Requirements
For apps to be featured:
- Icon: 192x192px transparent PNG
- Thumbnail: 784x442px with rounded corners, transparent PNG
- Screenshots: 1280x720px (PNG/JPG, optimize file size)
- Must demonstrate exceptional quality and user experience