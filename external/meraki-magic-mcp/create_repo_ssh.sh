#!/bin/bash
# Create GitHub repository using SSH

REPO_NAME="meraki-magic-mcp-enhanced"
DESCRIPTION="Enhanced Meraki Magic MCP with TUI, AI Assistant integration, and reusable framework support"
USERNAME="kmransom56"

echo "Creating GitHub repository: $REPO_NAME"
echo "Description: $DESCRIPTION"
echo ""

# Check if we have a GitHub token in environment
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN not set. You'll need to:"
    echo "   1. Create the repository manually at https://github.com/new"
    echo "   2. Or set GITHUB_TOKEN environment variable"
    echo ""
    echo "Repository name: $REPO_NAME"
    echo "Description: $DESCRIPTION"
    echo "Visibility: Public"
    echo ""
    echo "After creating, run:"
    echo "  git remote add new-origin git@github.com:$USERNAME/$REPO_NAME.git"
    echo "  git add ."
    echo "  git commit -m 'Enhanced version with TUI, AI integration, and reusable framework'"
    echo "  git push -u new-origin main"
    exit 1
fi

# Create repository using GitHub API
echo "Creating repository via GitHub API..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"$DESCRIPTION\",
    \"private\": false
  }")

# Check if repository was created
if echo "$RESPONSE" | grep -q '"id"'; then
    echo "✅ Repository created successfully!"
    echo ""
    echo "Repository URL: https://github.com/$USERNAME/$REPO_NAME"
    echo ""
    
    # Add remote
    echo "Adding SSH remote..."
    git remote add new-origin git@github.com:$USERNAME/$REPO_NAME.git 2>/dev/null || \
        git remote set-url new-origin git@github.com:$USERNAME/$REPO_NAME.git
    
    echo "✅ Remote added: new-origin"
    echo ""
    echo "Next steps:"
    echo "  git add ."
    echo "  git commit -m 'Enhanced version with TUI, AI integration, and reusable framework'"
    echo "  git push -u new-origin main"
else
    echo "❌ Failed to create repository"
    echo "Response: $RESPONSE"
    exit 1
fi
