#!/bin/bash
# Build and publish Laddr dashboard Docker image
# Usage: ./build-dashboard.sh [version]

set -e

VERSION=${1:-latest}
IMAGE_NAME="agnetlabs/laddrdashboard"

echo "🏗️  Building Laddr Dashboard Docker Image"
echo "================================================"
echo "Version: $VERSION"
echo "Image: $IMAGE_NAME:$VERSION"
echo ""

# Change to dashboard directory
cd "$(dirname "$0")"

# Build the image
echo "📦 Building Docker image..."
docker build -f Dockerfile.prod -t $IMAGE_NAME:$VERSION .

# Tag as latest if version provided
if [ "$VERSION" != "latest" ]; then
    echo "🏷️  Tagging as latest..."
    docker tag $IMAGE_NAME:$VERSION $IMAGE_NAME:latest
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "🧪 To test locally:"
echo "   docker run -p 5173:5173 $IMAGE_NAME:$VERSION"
echo ""
echo "📤 To push to Docker Hub:"
echo "   docker push $IMAGE_NAME:$VERSION"
if [ "$VERSION" != "latest" ]; then
    echo "   docker push $IMAGE_NAME:latest"
fi
echo ""
echo "📊 Image info:"
docker images $IMAGE_NAME:$VERSION --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
