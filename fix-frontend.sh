#!/bin/bash
set -e

echo "🔧 Fixing missing dependencies..."

cd /Users/alexkamer/f1_webapp/frontend

echo "📦 Installing class-variance-authority..."
npm install class-variance-authority

echo "✅ Done! The frontend should now work."
echo ""
echo "If the dev server is still running, it should auto-reload."
echo "If not, restart it with: npm run dev"
