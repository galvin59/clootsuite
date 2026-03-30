# ClootSuite — Cahier des charges

## 1. Vision

Un outil CLI pour publier une vidéo + texte d'accompagnement sur TikTok, Instagram et X en une seule commande. L'architecture est pensée pour exposer les mêmes fonctionnalités via une API HTTP demain.

```
cloot post video.mp4 --caption "Mon texte" --platforms tiktok,instagram,x
```

## 2. Périmètre v1 (CLI)

### Ce qu'on fait

- Poster une vidéo locale avec un texte sur 1 à 3 plateformes en une commande
- Authentification OAuth2 par plateforme (flow navigateur → callback localhost)
- Stockage sécurisé des tokens avec refresh automatique
- Retour clair : succès/échec par plateforme, URL du post si disponible

### Ce qu'on ne fait PAS (v1)

- Pas de scheduling (publication différée)
- Pas d'analytics / lecture de stats
- Pas de gestion multi-comptes
- Pas d'interface web ou API HTTP (prévu v2)

## 3. Stack technique

| Choix | Justification |
|-------|---------------|
| **Python 3.12+** | Écosystème HTTP mature, typage, rapide à itérer |
| **Click** | Framework CLI robuste, composable, bien documenté |
| **httpx** | Client HTTP async-ready (utile pour v2 API) |
| **keyring** | Stockage sécurisé des tokens (Keychain macOS, libsecret Linux) |
| **Pydantic v2** | Validation des configs et modèles — réutilisable tel quel en API FastAPI |

## 4. Architecture

```
clootsuite/
├── cli/                    # Couche CLI (Click)
│   ├── main.py             #   Point d'entrée, commande racine
│   ├── post.py             #   Commande `cloot post`
│   └── auth.py             #   Commande `cloot auth login/status/logout`
│
├── core/                   # Logique métier (indépendante du transport)
│   ├── publisher.py        #   Orchestrateur : dispatch vers les adapters
│   ├── models.py           #   PostRequest, PostResult, PlatformCredentials
│   └── auth_manager.py     #   Gestion tokens OAuth2 (store, refresh, revoke)
│
├── adapters/               # Un module par plateforme
│   ├── base.py             #   Classe abstraite PlatformAdapter
│   ├── tiktok.py           #   TikTok Content Posting API
│   ├── instagram.py        #   Instagram Graph API (Reels)
│   └── x.py                #   X API v2 (media upload + tweet)
│
├── oauth/                  # Serveur callback OAuth local
│   └── server.py           #   Serveur HTTP éphémère localhost:8080
│
└── config/
    └── settings.py         #   Chargement config (.env / fichier YAML)
```

### Principes clés

**Adapter pattern** — Chaque plateforme implémente la même interface :

```python
class PlatformAdapter(ABC):
    async def authenticate(self) -> Credentials: ...
    async def upload_video(self, file: Path, caption: str) -> PostResult: ...
    async def refresh_token(self, credentials: Credentials) -> Credentials: ...
```

**Core découplé du transport** — `publisher.py` ne sait pas s'il est appelé depuis Click ou depuis FastAPI. Il reçoit un `PostRequest` Pydantic, retourne un `PostResult`. Demain, exposer une API revient à brancher un `router.py` FastAPI sur le même `publisher.py`.

**Async-first** — Le core utilise `async/await` nativement. Les posts sur 3 plateformes se font en parallèle (`asyncio.gather`). La CLI wrappe avec `asyncio.run()`.

## 5. Modèles de données

```python
class PostRequest(BaseModel):
    video_path: Path
    caption: str
    platforms: list[Platform]  # enum: tiktok, instagram, x

class PostResult(BaseModel):
    platform: Platform
    success: bool
    post_url: str | None = None
    error: str | None = None

class Credentials(BaseModel):
    platform: Platform
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
```

## 6. Flux de publication par plateforme

### TikTok (Content Posting API — Sandbox)

1. **Auth** : OAuth2 → `https://www.tiktok.com/v2/auth/authorize/` avec scopes `user.info.basic,video.publish,video.upload`
2. **Upload** : `POST /v2/post/publish/video/init/` (chunk upload via `push_by_file`)
3. **Publish** : Direct Post activé → publication immédiate
4. Credentials : Client Key `7623057824385468423` (Sandbox)

### Instagram (Graph API — Reels)

1. **Auth** : OAuth2 Facebook → token longue durée (60 jours)
2. **Upload** : `POST /{ig-user-id}/media` avec `media_type=REELS`, `video_url` ou upload
3. **Publish** : `POST /{ig-user-id}/media_publish` avec le container ID
4. App ID : `1636759747361854`

### X (API v2 + Media Upload)

1. **Auth** : OAuth 2.0 PKCE → scopes `tweet.write`, `users.read`
2. **Upload** : Media Upload API (chunked) → `media_id`
3. **Publish** : `POST /2/tweets` avec `media.media_ids`
4. App ID : `32675879`

## 7. Commandes CLI

```bash
# Authentification
cloot auth login tiktok          # Ouvre le navigateur, OAuth, stocke le token
cloot auth login instagram
cloot auth login x
cloot auth status                # Affiche l'état des tokens par plateforme
cloot auth logout tiktok         # Révoque et supprime le token

# Publication
cloot post video.mp4 \
  --caption "Découvre Gamies!" \
  --platforms tiktok,instagram,x

# Sortie :
# ✓ TikTok  — https://www.tiktok.com/@gamiesapp/video/...
# ✓ Instagram — https://www.instagram.com/reel/...
# ✗ X — Error: Video too long (max 140s)
```

## 8. Configuration

Fichier `~/.clootsuite/config.yaml` :

```yaml
tiktok:
  client_key: "..."
  client_secret: "..."
  redirect_uri: "http://localhost:8080/callback"
  sandbox: true

instagram:
  app_id: "..."
  app_secret: "..."
  redirect_uri: "http://localhost:8080/callback"

x:
  client_id: "..."
  client_secret: "..."
  redirect_uri: "http://localhost:8080/callback"
```

Les tokens ne sont **jamais** dans ce fichier — ils sont dans le keyring OS.

## 9. Gestion d'erreurs

| Situation | Comportement |
|-----------|-------------|
| Token expiré | Refresh automatique, retry transparent |
| Refresh échoué | Message clair "Run `cloot auth login <platform>`" |
| Vidéo trop lourde | Erreur avant upload avec les limites de la plateforme |
| Format non supporté | Erreur avec les formats acceptés |
| 1 plateforme échoue | Les autres continuent, résumé à la fin |
| Pas de connexion | Fail fast avec message explicite |

## 10. Étapes de développement

| Phase | Contenu | Critère de validation |
|-------|---------|----------------------|
| **P0** | Squelette projet, models Pydantic, adapter base | `cloot --help` fonctionne |
| **P1** | OAuth flow + token storage (1 plateforme : TikTok) | `cloot auth login tiktok` stocke un token valide |
| **P2** | Upload + publish TikTok (Sandbox) | `cloot post video.mp4 --platforms tiktok` publie en Sandbox |
| **P3** | Adapter Instagram (Reels) | Publication Reel via CLI |
| **P4** | Adapter X (media + tweet) | Publication vidéo+texte via CLI |
| **P5** | Publication multi-plateforme parallèle | `--platforms tiktok,instagram,x` en une commande |
| **P6** | Polish : retry, logs, validation vidéo, --dry-run | Outil fiable au quotidien |

## 11. Évolution v2 (API HTTP)

L'architecture permet d'ajouter une couche API sans toucher au core :

```
clootsuite/
├── api/                    # Nouveau : couche FastAPI
│   ├── router.py           #   POST /publish, GET /auth/status
│   └── dependencies.py     #   Injection du Publisher
```

Le `Publisher` et les `Adapters` sont réutilisés tels quels. Pydantic sert à la fois de validation CLI et de schéma API OpenAPI.
