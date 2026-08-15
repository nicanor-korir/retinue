# Deviant Frontend Dashboard

A modern, responsive Next.js 14 dashboard for monitoring and managing your AI agent company.

## Features

- **Real-time Updates**: Auto-refreshing data with React Query
- **Beautiful UI**: Modern design with TailwindCSS and custom components
- **Dark Mode**: Full dark mode support with theme switcher
- **Responsive**: Works perfectly on desktop, tablet, and mobile
- **Type-Safe**: Full TypeScript coverage
- **Fast**: Optimized with Next.js 14 App Router

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: React Query (TanStack Query)
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod validation
- **Icons**: Lucide React
- **Charts**: Recharts (optional)
- **Animations**: Framer Motion

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
Copy-Item .env.local.example .env.local

# Start development server
npm run dev
```

The dashboard will be available at http://localhost:3000

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Available Scripts

```powershell
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router pages
│   │   ├── page.tsx           # Dashboard home
│   │   ├── projects/          # Projects pages
│   │   ├── agents/            # Agents pages
│   │   ├── tasks/             # Tasks pages
│   │   ├── messages/          # Messages pages
│   │   ├── escalations/       # Escalations pages
│   │   ├── audit/             # Audit log pages
│   │   ├── layout.tsx         # Root layout
│   │   ├── providers.tsx      # React Query + Theme providers
│   │   └── globals.css        # Global styles
│   ├── components/            # Reusable components
│   │   ├── ui/                # Base UI components (Button, Card, etc.)
│   │   ├── layout/            # Layout components (Sidebar, etc.)
│   │   ├── projects/          # Project-specific components
│   │   └── theme-provider.tsx # Dark mode provider
│   ├── hooks/                 # Custom React hooks
│   │   └── useApi.ts          # API hooks with React Query
│   ├── lib/                   # Utilities
│   │   ├── api.ts             # API client (Axios)
│   │   └── utils.ts           # Helper functions
│   └── types/                 # TypeScript types
│       └── api.ts             # API type definitions
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
└── README.md
```

## Key Features

### Dashboard Pages

1. **Home Dashboard** (`/`)
   - System overview with key metrics
   - Recent projects, tasks, and messages
   - Agent status at a glance
   - Auto-refreshes every 10 seconds

2. **Projects** (`/projects`)
   - List all projects with status filters
   - Create new projects with validation
   - View project details with task breakdown
   - Real-time progress tracking

3. **Agents** (`/agents`)
   - Monitor all 7 agents
   - Real-time availability status
   - Task completion metrics
   - Organization hierarchy view

4. **Tasks** (`/tasks`)
   - View all tasks across projects
   - Filter by status
   - Task assignment tracking
   - View code output

5. **Messages** (`/messages`)
   - Agent-to-agent communications
   - Filter by priority and type
   - Unread message indicators
   - Real-time updates every 5 seconds

6. **Escalations** (`/escalations`)
   - Track issues between agents
   - View resolution status

7. **Audit Log** (`/audit`)
   - Complete action history
   - Detailed event tracking

### Components

#### UI Components (`src/components/ui/`)

- **Button**: Multiple variants (default, outline, ghost, etc.)
- **Card**: Container with header, content, footer
- **Badge**: Status indicators with color variants
- All components are accessible and keyboard-navigable

#### Layout Components

- **DashboardLayout**: Main layout with sidebar and top bar
- **Sidebar**: Responsive navigation with mobile support
- **Theme Switcher**: Toggle between light and dark modes

### API Integration

All API calls use React Query for:
- Automatic caching
- Background refetching
- Optimistic updates
- Loading and error states

```typescript
// Example usage
import { useProjects, useCreateProject } from "@/hooks/useApi";

function MyComponent() {
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();

  const handleCreate = async (data) => {
    await createProject.mutateAsync(data);
  };

  // ...
}
```

### Real-time Updates

Data automatically refreshes at different intervals:
- **Health**: Every 30 seconds
- **Projects**: Every 15 seconds
- **Agent Status**: Every 15 seconds
- **Tasks**: Every 10 seconds
- **Dashboard**: Every 10 seconds
- **Messages**: Every 5 seconds (fastest for real-time feel)

## Customization

### Theme Colors

Edit `tailwind.config.ts` to customize colors:

```typescript
theme: {
  extend: {
    colors: {
      primary: "hsl(var(--primary))",
      // Add your custom colors
    }
  }
}
```

Update CSS variables in `src/app/globals.css`:

```css
:root {
  --primary: 240 5.9% 10%;
  --secondary: 240 4.8% 95.9%;
  /* Your custom variables */
}
```

### Adding New Pages

1. Create page file: `src/app/your-page/page.tsx`
2. Add route to sidebar: `src/components/layout/dashboard-layout.tsx`
3. Create API hook if needed: `src/hooks/useApi.ts`

### Adding New API Endpoints

1. Add type definitions: `src/types/api.ts`
2. Create API function: `src/lib/api.ts`
3. Create React Query hook: `src/hooks/useApi.ts`

## Performance Optimizations

- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: Use Next.js `<Image>` component
- **Bundle Analysis**: Run `npm run build` to see bundle sizes
- **React Query Caching**: Reduces unnecessary API calls
- **Memoization**: Components use React.memo where appropriate

## Responsive Design

The dashboard is fully responsive with breakpoints:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

Sidebar automatically collapses to overlay on mobile.

## Accessibility

- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Backend Connection Issues

If you see connection errors:

1. Ensure backend is running on http://localhost:8000
2. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Verify CORS is enabled in backend

### Build Errors

```powershell
# Clear Next.js cache
Remove-Item -Recurse -Force .next

# Reinstall dependencies
Remove-Item -Recurse -Force node_modules
npm install

# Rebuild
npm run build
```

### Type Errors

```powershell
# Run type checker
npm run type-check
```

## Development Tips

1. **Hot Reload**: Changes auto-reload in dev mode
2. **React Query Devtools**: Available in dev mode (bottom-left icon)
3. **TypeScript**: Use strict mode for better type safety
4. **Linting**: Run `npm run lint` before committing

## Production Deployment

```powershell
# Build
npm run build

# Test production build locally
npm start

# Deploy to your platform
# (Vercel, Netlify, AWS, etc.)
```

### Recommended Platforms

- **Vercel** (recommended for Next.js)
- **Netlify**
- **AWS Amplify**
- **Azure Static Web Apps**

## Environment Variables for Production

```env
NEXT_PUBLIC_API_URL=https://your-production-api.com
```

## Contributing

When adding new features:

1. Follow existing code patterns
2. Add TypeScript types
3. Use existing components where possible
4. Test on mobile and desktop
5. Update this README if needed

## License

Same as parent project.

---

**Built with Next.js 14 + TailwindCSS + React Query**

For questions or issues, refer to the main Deviant documentation.
