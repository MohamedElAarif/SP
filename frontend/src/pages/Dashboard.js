import React, { useState, useEffect } from 'react';
import { scrapeAPI } from '../services/api';
import { Play, Globe, Settings, Download, Trash2, Eye } from 'lucide-react';
import toast from 'react-hot-toast';
import ScrapingForm from '../components/ScrapingForm';
import ResultsTable from '../components/ResultsTable';
import ExportButtons from '../components/ExportButtons';

function Dashboard() {
  const [scrapeJobs, setScrapeJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleScrape = async (scrapeData) => {
    setLoading(true);
    try {
      const response = await scrapeAPI.createScrapeJob(scrapeData);
      const job = response.data;
      
      setScrapeJobs(prev => [job, ...prev]);
      setCurrentJob(job);
      
      // Poll for job completion
      pollJobStatus(job.id);
      
      toast.success('Scraping job started!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start scraping job');
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await scrapeAPI.getScrapeResult(jobId);
        const job = response.data;
        
        setScrapeJobs(prev => 
          prev.map(j => j.id === jobId ? job : j)
        );
        
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(pollInterval);
          if (job.status === 'completed') {
            setCurrentJob(job);
            toast.success('Scraping completed!');
          } else {
            toast.error('Scraping failed: ' + job.error_message);
          }
        }
      } catch (error) {
        clearInterval(pollInterval);
        toast.error('Error checking job status');
      }
    }, 2000);

    // Clear interval after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const deleteJob = async (jobId) => {
    try {
      await scrapeAPI.deleteScrapeJob(jobId);
      setScrapeJobs(prev => prev.filter(job => job.id !== jobId));
      if (currentJob?.id === jobId) {
        setCurrentJob(null);
      }
      toast.success('Job deleted successfully');
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  const viewJob = (job) => {
    setCurrentJob(job);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Web Scraping Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Extract data from websites using CSS selectors or XPath expressions
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Scraping Form */}
        <div className="card">
          <div className="flex items-center mb-4">
            <Settings className="h-5 w-5 text-primary-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Scraping Configuration</h2>
          </div>
          <ScrapingForm onSubmit={handleScrape} loading={loading} />
        </div>

        {/* Recent Jobs */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Globe className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Recent Jobs</h2>
            </div>
          </div>
          
          {scrapeJobs.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No scraping jobs yet</p>
          ) : (
            <div className="space-y-2">
              {scrapeJobs.slice(0, 5).map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {job.url}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      job.status === 'completed' ? 'bg-green-100 text-green-800' :
                      job.status === 'failed' ? 'bg-red-100 text-red-800' :
                      job.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {job.status}
                    </span>
                    <button
                      onClick={() => viewJob(job)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                      title="View details"
                    >
                      <Eye className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => deleteJob(job.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                      title="Delete job"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Results Section */}
      {currentJob && currentJob.status === 'completed' && currentJob.result_data && (
        <div className="mt-8 card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Download className="h-5 w-5 text-primary-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">Scraping Results</h2>
            </div>
            <ExportButtons jobId={currentJob.id} />
          </div>
          <ResultsTable data={currentJob.result_data} />
        </div>
      )}

      {/* Error Display */}
      {currentJob && currentJob.status === 'failed' && (
        <div className="mt-8 card">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-red-800 mb-2">Scraping Failed</h3>
            <p className="text-red-700">{currentJob.error_message}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
