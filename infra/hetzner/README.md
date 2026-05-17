# Hetzner deploy reference

This is the minimum you need to deploy `bato-learning` on a single Hetzner CX22.
For the full walkthrough see [`08-hetzner-docker`](../../web/src/content/docs/08-hetzner-docker/01-setup.mdx).

## Bootstrap (run on the host)

```bash
# 1. Docker + compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. Pull repo and copy env
git clone https://github.com/you/bato-learning.git
cd bato-learning
cp .env.example .env
# fill ANTHROPIC_API_KEY and any host-specific overrides

# 3. Bring it up
docker compose -f docker-compose.yml -f infra/hetzner/compose.prod.yml up -d

# 4. Logs
docker compose logs -f api web traefik
```

## What's intentionally NOT here

- Kubernetes manifests. See module 10 for when (not) to migrate.
- Multi-region. Not needed at single-CX22 scale.
- Cluster-mode Postgres. CNPG belongs in module 10.
