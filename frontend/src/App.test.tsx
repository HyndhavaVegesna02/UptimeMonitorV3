import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import App from './App';
import { server } from './mocks/server';
import { http, HttpResponse } from 'msw';

describe('Uptime Monitor V3 Frontend Shell', () => {
  beforeEach(() => {
    // Reset window.location.hash to default dashboard
    window.location.hash = '';
    window.dispatchEvent(new Event('hashchange'));
  });

  it('renders the persistent navigation with all six tabs', () => {
    render(<App />);

    expect(screen.getByText('Uptime Monitor V3')).toBeInTheDocument();
    
    // Check navigation items
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Availability' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Approvals' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Check History' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Maintenance' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Publications' })).toBeInTheDocument();
  });

  it('initially displays the Dashboard active and loads components', async () => {
    render(<App />);

    // Active tab indicator check
    const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(dashboardLink).toHaveClass('nav-state-active');

    // Loading indicator should appear
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

    // Eventually the components list should load
    await waitFor(() => {
      expect(screen.getByTestId('components-list')).toBeInTheDocument();
    });

    // Check mock data is rendered
    expect(screen.getByText('Payment Gateway')).toBeInTheDocument();
    expect(screen.getByText('payment-gateway')).toBeInTheDocument();
    expect(screen.getByText('Operational')).toBeInTheDocument();

    expect(screen.getByText('Authentication Service')).toBeInTheDocument();
    expect(screen.getByText('Degraded')).toBeInTheDocument();

    expect(screen.getByText('Inventory Database')).toBeInTheDocument();
    expect(screen.getByText('Outage')).toBeInTheDocument();

    expect(screen.getByText('Email Worker')).toBeInTheDocument();
    expect(screen.getByTestId('status-badge-maintenance')).toHaveTextContent('Maintenance');
  });

  it('switches tabs and displays placeholder panels', async () => {
    render(<App />);

    // Initially Dashboard is active
    await waitFor(() => {
      expect(screen.getByTestId('components-list')).toBeInTheDocument();
    });

    // Click on Availability
    const availabilityLink = screen.getByRole('link', { name: 'Availability' });
    fireEvent.click(availabilityLink);

    // Wait for JSDOM location update to complete
    await waitFor(() => {
      expect(window.location.hash).toBe('#availability');
    });

    // Active indicator should move
    expect(availabilityLink).toHaveClass('nav-state-active');
    expect(screen.getByRole('link', { name: 'Dashboard' })).not.toHaveClass('nav-state-active');

    // Placeholder panel should be shown
    expect(screen.getByTestId('placeholder-panel')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Availability', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('The Availability panel is coming soon in a future sprint.')).toBeInTheDocument();
  });

  it('handles error state and allows retrying', async () => {
    // Override the MSW handler to return an error status
    server.use(
      http.get('/api/v1/components', () => {
        return new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' });
      })
    );

    render(<App />);

    // Loading indicator should appear first
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

    // Eventually error message should appear
    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
    });

    expect(screen.getByText('Failed to Load Components')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch components: 500 Internal Server Error')).toBeInTheDocument();

    // Now restore normal behavior (remove runtime overrides)
    server.resetHandlers();

    // Click retry button
    const retryButton = screen.getByRole('button', { name: 'Try Again' });
    fireEvent.click(retryButton);

    // Loading indicator should appear again
    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

    // Eventually the components should load successfully
    await waitFor(() => {
      expect(screen.getByTestId('components-list')).toBeInTheDocument();
    });
    expect(screen.getByText('Payment Gateway')).toBeInTheDocument();
  });
});
