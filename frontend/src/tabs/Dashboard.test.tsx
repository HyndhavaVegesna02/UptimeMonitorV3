import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { Dashboard } from './Dashboard';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import type { ComponentDTO } from '../apiClient';

/* ─────────────────────────────────────────────────────────────────────────────
   MSW baseline: four components covering all four health states.
   We assert user-visible behavior (text, roles), NOT the mocked values directly.
   ───────────────────────────────────────────────────────────────────────────── */

describe('Dashboard tab', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  /* ── Success ────────────────────────────────────────────────────────────── */
  describe('success state', () => {
    it('shows a loading indicator while fetching', () => {
      render(<Dashboard />);
      expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
    });

    it('renders all four components once data loads', async () => {
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('components-list')).toBeInTheDocument();
      });

      // Component names from mock data
      expect(screen.getByText('Payment Gateway')).toBeInTheDocument();
      expect(screen.getByText('Authentication Service')).toBeInTheDocument();
      expect(screen.getByText('Inventory Database')).toBeInTheDocument();
      expect(screen.getByText('Email Worker')).toBeInTheDocument();
    });

    it('maps "up" status to the Operational badge', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      // Payment Gateway is 'up' in handlers.ts
      expect(screen.getByTestId('status-badge-up')).toHaveTextContent('Operational');
    });

    it('maps "degraded" status to the Degraded badge', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      // Authentication Service is 'degraded'
      expect(screen.getByTestId('status-badge-degraded')).toHaveTextContent('Degraded');
    });

    it('maps "down" status to the Outage badge', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      // Inventory Database is 'down'
      expect(screen.getByTestId('status-badge-down')).toHaveTextContent('Outage');
    });

    it('maps "maintenance" status to the Maintenance badge', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      // Email Worker is 'maintenance'
      expect(screen.getByTestId('status-badge-maintenance')).toHaveTextContent(
        'Maintenance'
      );
    });

    it('renders an accessible table with column headers', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );

      const table = screen.getByRole('table', { name: 'Component status' });
      expect(table).toBeInTheDocument();

      // <th scope="col"> columns
      expect(
        screen.getByRole('columnheader', { name: 'Component Name' })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('columnheader', { name: 'Identifier' })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('columnheader', { name: 'Status' })
      ).toBeInTheDocument();
    });

    it('renders component identifiers in the table', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      expect(screen.getByText('payment-gateway')).toBeInTheDocument();
    });

    it('handles an unknown status defensively without crashing', async () => {
      const withUnknown: ComponentDTO[] = [
        { id: 'mystery-svc', name: 'Mystery Service', status: 'unknown-state' },
      ];
      server.use(
        http.get('/api/v1/components', () => HttpResponse.json(withUnknown))
      );

      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );

      // Should render the raw status string, not crash
      expect(screen.getByTestId('status-badge-unknown')).toHaveTextContent(
        'unknown-state'
      );
    });
  });

  /* ── Empty ──────────────────────────────────────────────────────────────── */
  describe('empty state', () => {
    it('shows the empty state message when the API returns []', async () => {
      server.use(
        http.get('/api/v1/components', () => HttpResponse.json([]))
      );

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      });

      expect(
        screen.getByText('No components configured yet.')
      ).toBeInTheDocument();

      // Neither the table nor an error panel should be present
      expect(screen.queryByTestId('components-list')).not.toBeInTheDocument();
      expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
    });
  });

  /* ── Error + Retry ──────────────────────────────────────────────────────── */
  describe('error state and retry', () => {
    it('shows an error panel on a 500 response', async () => {
      server.use(
        http.get('/api/v1/components', () =>
          new HttpResponse(null, {
            status: 500,
            statusText: 'Internal Server Error',
          })
        )
      );

      render(<Dashboard />);

      // Loading appears first
      expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
      });

      expect(screen.getByText('Failed to Load Components')).toBeInTheDocument();
      expect(
        screen.getByText('Failed to fetch components: 500 Internal Server Error')
      ).toBeInTheDocument();
    });

    it('shows a "Try Again" button in the error panel', async () => {
      server.use(
        http.get('/api/v1/components', () =>
          new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' })
        )
      );

      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      );

      expect(
        screen.getByRole('button', { name: 'Try Again' })
      ).toBeInTheDocument();
    });

    it('retries and recovers after handler reset', async () => {
      server.use(
        http.get('/api/v1/components', () =>
          new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' })
        )
      );

      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
      );

      // Restore normal handler (the baseline four-component response)
      server.resetHandlers();

      // Click retry
      fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));

      // Loading indicator appears again
      expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();

      // Success state recovers
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      expect(screen.getByText('Payment Gateway')).toBeInTheDocument();
    });
  });

  /* ── Refresh button ─────────────────────────────────────────────────────── */
  describe('Refresh button', () => {
    it('is present after data loads', async () => {
      render(<Dashboard />);
      await waitFor(() =>
        expect(screen.getByTestId('components-list')).toBeInTheDocument()
      );
      expect(
        screen.getByRole('button', { name: /refresh/i })
      ).toBeInTheDocument();
    });
  });
});
