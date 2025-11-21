## Design System

### Typography
- **Font Family**: Work Sans (primary), Inter (fallback)
- **Base Font Size**: 14px
- **Font Weights**: 300, 400, 500, 600, 700
- Use semantic heading hierarchy (h1-h4)
- Avoid custom font sizes/weights unless specifically required

### Color Palette
- **Neutral Base**: White backgrounds with glass morphism effects
- **Text**: Black to gray-600 gradients for hierarchy
- **Chart Colors**: Custom palette (yellow #f2e437, green #8bcd50, orange #f6a21e, cyan #75e6da, etc.)
- **Glass Effects**: `backdrop-blur-xl bg-white/40 border-white/20`

### Effects & Animations
- **Liquid Glass**: Use `liquid-glass-icon` class for interactive elements
- **Hover States**: Scale transforms (1.05), shadow increases, color transitions
- **Motion**: Use Motion (motion/react) for smooth animations
- **Timing**: 300ms standard, 1000ms for background color changes
