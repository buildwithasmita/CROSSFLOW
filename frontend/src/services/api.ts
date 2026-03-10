import axios from 'axios';
import { GCSCustomer, PropensityScore } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const scoreSingleCustomer = async (customer: GCSCustomer): Promise<PropensityScore> => {
  const response = await api.post('/crosssell/score/single', customer);
  return response.data;
};

export const scoreBatchCustomers = async (
  customers: GCSCustomer[],
  includeExplanations = true
): Promise<{ results: PropensityScore[]; summary: any; processing_time_seconds: number }> => {
  const response = await api.post('/crosssell/score/batch', {
    customers,
    include_explanations: includeExplanations,
  });
  return response.data;
};

export const getSampleCustomers = async (limit = 50): Promise<GCSCustomer[]> => {
  const response = await api.get(`/crosssell/customers/sample?limit=${limit}`);
  return response.data;
};

export const getFeatureImportance = async (): Promise<any[]> => {
  const response = await api.get('/crosssell/analytics/feature-importance');
  return response.data;
};

export const healthCheck = async (): Promise<any> => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
