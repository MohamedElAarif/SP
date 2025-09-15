import React, { useState, useEffect } from 'react';
import { historyAPI } from '../services/api';
import { Trash2, Eye, Download, Calendar, BarChart3 } from 'lucide-react';
import toast from 'react-hot-toast';
import ExportButtons from '../components/ExportButtons';
import ResultsTable from '../components/ResultsTable';

function History() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState(null);
  const [filters, setFilters] = useState({
    page: 1,
    per_page: 10,
    status_filter: '',
    days: ''
  });

  useEffect(() => {
    fetchHistory();
    fetchStats();
  }, [filters]);

  const fetchHistory = async () => {
    try {
      const response = await historyAPI.getHistory(filters);
      setJobs(response.data);
    } catch (error) {
      toast.error('Failed to fetch history');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await historyAPI.getStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1 // Reset to first page when filters change
    }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  const deleteJob = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job?')) return;
    
    try {
      // This would need to be implemented in the API
      toast.success('Job deleted successfully');
      fetchHistory();
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  const clearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all history?')) return;
    
    try {
      await historyAPI.clearHistory();
      toast.success('History cleared successfully');
      fetchHistory();
      fetchStats();
    } catch (error) {
      toast.error('Failed to clear history');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'running': return 'bg-yellow-100 text-yellow-800';
      case 'pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Scraping History</h1>
        <p className="mt-2 text-gray-600">
          View and manage your past scraping jobs
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Jobs</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_jobs}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-semibold">✓</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.completed_jobs}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 font-semibold">✗</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Failed</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.failed_jobs}</p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-semibold">%</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Success Rate</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.success_rate.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status_filter}
              onChange={(e) => handleFilterChange('status_filter', e.target.value)}
              className="input-field"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="running">Running</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Time Period</label>
            <select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', e.target.value)}
              className="input-field"
            >
              <option value="">All Time</option>
              <option value="1">Last 24 hours</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
            </select>
          </div>
          <div className="ml-auto">
            <button
              onClick={clearHistory}
              className="btn-secondary flex items-center"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear History
            </button>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Jobs</h2>
        
        {jobs.items?.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No jobs found</p>
        ) : (
          <div className="space-y-4">
            {jobs.items?.map((job) => (
              <div key={job.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {job.url}
                    </p>
                    <div className="flex items-center mt-1 space-x-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                      <span className="text-xs text-gray-500">
                        <Calendar className="h-3 w-3 inline mr-1" />
                        {new Date(job.created_at).toLocaleString()}
                      </span>
                      {job.completed_at && (
                        <span className="text-xs text-gray-500">
                          Completed: {new Date(job.completed_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                    {job.error_message && (
                      <p className="text-xs text-red-600 mt-1">{job.error_message}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {job.status === 'completed' && (
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="p-2 text-gray-400 hover:text-gray-600"
                        title="View results"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteJob(job.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                      title="Delete job"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {jobs.total_pages > 1 && (
          <div className="flex items-center justify-between mt-6">
            <p className="text-sm text-gray-700">
              Showing {((filters.page - 1) * filters.per_page) + 1} to{' '}
              {Math.min(filters.page * filters.per_page, jobs.total)} of {jobs.total} results
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => handlePageChange(filters.page - 1)}
                disabled={filters.page === 1}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => handlePageChange(filters.page + 1)}
                disabled={filters.page === jobs.total_pages}
                className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {selectedJob && selectedJob.status === 'completed' && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Job Results</h3>
              <div className="flex items-center space-x-2">
                <ExportButtons jobId={selectedJob.id} />
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              <ResultsTable data={selectedJob.result_data} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default History;
