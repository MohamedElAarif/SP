import React, { useState } from 'react';
import { Plus, Trash2, Globe } from 'lucide-react';

function ScrapingForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    url: '',
    use_selenium: false,
    selectors: [
      { field: 'title', selector: 'h1, h2, h3' },
      { field: 'links', selector: 'a[href]' },
    ]
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSelectorChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      selectors: prev.selectors.map((sel, i) => 
        i === index ? { ...sel, [field]: value } : sel
      )
    }));
  };

  const addSelector = () => {
    setFormData(prev => ({
      ...prev,
      selectors: [...prev.selectors, { field: '', selector: '' }]
    }));
  };

  const removeSelector = (index) => {
    setFormData(prev => ({
      ...prev,
      selectors: prev.selectors.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.url) {
      alert('Please enter a URL');
      return;
    }

    if (formData.selectors.length === 0) {
      alert('Please add at least one selector');
      return;
    }

    // Convert selectors array to object
    const selectorsObj = {};
    formData.selectors.forEach(sel => {
      if (sel.field && sel.selector) {
        selectorsObj[sel.field] = sel.selector;
      }
    });

    if (Object.keys(selectorsObj).length === 0) {
      alert('Please add valid selectors');
      return;
    }

    onSubmit({
      url: formData.url,
      use_selenium: formData.use_selenium,
      selectors: selectorsObj
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* URL Input */}
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
          Website URL
        </label>
        <div className="relative">
          <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="url"
            id="url"
            name="url"
            value={formData.url}
            onChange={handleChange}
            className="input-field pl-10"
            placeholder="https://example.com"
            required
          />
        </div>
      </div>

      {/* Selenium Option */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="use_selenium"
          name="use_selenium"
          checked={formData.use_selenium}
          onChange={handleChange}
          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
        />
        <label htmlFor="use_selenium" className="ml-2 block text-sm text-gray-700">
          Use Selenium for JavaScript-heavy pages
        </label>
      </div>

      {/* Selectors */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Data Selectors
        </label>
        <div className="space-y-3">
          {formData.selectors.map((selector, index) => (
            <div key={index} className="flex space-x-2">
              <input
                type="text"
                placeholder="Field name (e.g., title, price)"
                value={selector.field}
                onChange={(e) => handleSelectorChange(index, 'field', e.target.value)}
                className="flex-1 input-field"
              />
              <input
                type="text"
                placeholder="CSS selector (e.g., h1, .price)"
                value={selector.selector}
                onChange={(e) => handleSelectorChange(index, 'selector', e.target.value)}
                className="flex-1 input-field"
              />
              <button
                type="button"
                onClick={() => removeSelector(index)}
                className="p-2 text-red-600 hover:text-red-800"
                disabled={formData.selectors.length === 1}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={addSelector}
          className="mt-2 flex items-center text-sm text-primary-600 hover:text-primary-800"
        >
          <Plus className="h-4 w-4 mr-1" />
          Add Selector
        </button>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full btn-primary flex items-center justify-center"
      >
        {loading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Scraping...
          </>
        ) : (
          <>
            <Play className="h-4 w-4 mr-2" />
            Start Scraping
          </>
        )}
      </button>
    </form>
  );
}

export default ScrapingForm;
