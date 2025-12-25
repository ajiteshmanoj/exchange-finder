#!/bin/bash

# Tailwind CSS Setup Script for NTU Exchange Finder Frontend

echo "🔧 Setting up Tailwind CSS..."
echo ""

# Step 1: Remove old node_modules and package-lock.json
echo "📦 Step 1: Cleaning old dependencies..."
rm -rf node_modules package-lock.json

# Step 2: Install dependencies
echo "📦 Step 2: Installing fresh dependencies..."
npm install

# Step 3: Verify Tailwind version
echo ""
echo "✅ Step 3: Verifying Tailwind CSS installation..."
npm list tailwindcss

# Step 4: Check if PostCSS config exists
echo ""
echo "✅ Step 4: Checking configuration files..."
if [ -f "postcss.config.js" ]; then
    echo "   ✓ postcss.config.js exists"
else
    echo "   ✗ postcss.config.js missing"
fi

if [ -f "tailwind.config.js" ]; then
    echo "   ✓ tailwind.config.js exists"
else
    echo "   ✗ tailwind.config.js missing"
fi

# Step 5: Done
echo ""
echo "✨ Setup complete! You can now run:"
echo "   npm run dev"
echo ""
