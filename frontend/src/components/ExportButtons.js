import React, { useState } from 'react';
import { scrapeAPI } from '../services/api';
import { Download, FileText, File, Database, Table } from 'lucide-react';
import toast from 'react-hot-toast';

function ExportButtons({ jobId }) {
  const [exporting, setExporting] = useState(null);

  const handleExport = async (format) => {
    setExporting(format);
    try {
      let response;
      let filename;
      
      switch (format) {
        case 'csv':
          response = await scrapeAPI.exportCSV(jobId);
          filename = 'scraped_data.csv';
          break;
        case 'json':
          response = await scrapeAPI.exportJSON(jobId);
          filename = 'scraped_data.json';
          break;
        case 'pdf':
          response = await scrapeAPI.exportPDF(jobId);
          filename = 'scraped_data.pdf';
          break;
        case 'excel':
          response = await scrapeAPI.exportExcel(jobId);
          filename = 'scraped_data.xlsx';
          break;
        default:
          throw new Error('Unknown export format');
      }

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success(`Data exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error(`Failed to export as ${format.toUpperCase()}`);
    } finally {
      setExporting(null);
    }
  };

  const exportOptions = [
    { format: 'csv', label: 'CSV', icon: Table, color: 'text-green-600 hover:text-green-800' },
    { format: 'json', label: 'JSON', icon: Database, color: 'text-blue-600 hover:text-blue-800' },
    { format: 'pdf', label: 'PDF', icon: FileText, color: 'text-red-600 hover:text-red-800' },
    { format: 'excel', label: 'Excel', icon: File, color: 'text-green-600 hover:text-green-800' },
  ];

  return (
    <div className="flex space-x-2">
      {exportOptions.map(({ format, label, icon: Icon, color }) => (
        <button
          key={format}
          onClick={() => handleExport(format)}
          disabled={exporting === format}
          className={`flex items-center px-3 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed ${color}`}
        >
          {exporting === format ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
          ) : (
            <Icon className="h-4 w-4 mr-2" />
          )}
          {label}
        </button>
      ))}
    </div>
  );
}

export default ExportButtons;
