import React, { useMemo } from 'react';
import { useTable } from 'react-table';

function ResultsTable({ data }) {
  // Filter out metadata and prepare data for table
  const tableData = useMemo(() => {
    if (!data || typeof data !== 'object') return [];
    
    const { _metadata, ...scrapedData } = data;
    const maxLength = Math.max(
      ...Object.values(scrapedData).map(values => 
        Array.isArray(values) ? values.length : 1
      )
    );
    
    const rows = [];
    for (let i = 0; i < maxLength; i++) {
      const row = {};
      Object.entries(scrapedData).forEach(([key, values]) => {
        if (Array.isArray(values)) {
          row[key] = values[i] || '';
        } else {
          row[key] = i === 0 ? values : '';
        }
      });
      rows.push(row);
    }
    
    return rows;
  }, [data]);

  const columns = useMemo(() => {
    if (tableData.length === 0) return [];
    
    return Object.keys(tableData[0]).map(key => ({
      Header: key.charAt(0).toUpperCase() + key.slice(1),
      accessor: key,
      Cell: ({ value }) => (
        <div className="max-w-xs truncate" title={value}>
          {value}
        </div>
      )
    }));
  }, [tableData]);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({
    columns,
    data: tableData,
  });

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data available
      </div>
    );
  }

  if (tableData.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data found with the specified selectors
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table {...getTableProps()} className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th
                  {...column.getHeaderProps()}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column.render('Header')}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()} className="bg-white divide-y divide-gray-200">
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()} className="hover:bg-gray-50">
                {row.cells.map(cell => (
                  <td
                    {...cell.getCellProps()}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                  >
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default ResultsTable;
