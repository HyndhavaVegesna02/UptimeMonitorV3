import { http, HttpResponse } from 'msw';
import type { ComponentDTO } from '../apiClient';

export const handlers = [
  http.get('/api/v1/components', () => {
    const mockComponents: ComponentDTO[] = [
      { id: 'payment-gateway', name: 'Payment Gateway', status: 'up' },
      { id: 'auth-service', name: 'Authentication Service', status: 'degraded' },
      { id: 'inventory-db', name: 'Inventory Database', status: 'down' },
      { id: 'email-worker', name: 'Email Worker', status: 'maintenance' }
    ];
    return HttpResponse.json(mockComponents);
  })
];
