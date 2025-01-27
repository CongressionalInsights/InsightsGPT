import React, { useState, useEffect, useCallback } from 'react'; // PLEASE CLARIFY: Are you intending to run this in a standard web environment (bundled with Rollup) or in a true React Native environment (e.g., with Expo, iOS/Android)? If you want a standard web environment, we can rely on typical React DOM elements. If you want a React Native environment, we typically do not bundle with Rollup. The code below is set up for a browser-based React app with standard HTML components, not react-native or react-native-web. We preserve your existing test cases. We do not modify them. We add new tests if needed.

/*
  Adding extra search-limiting factors:
    1) Time range (today, yesterday, this week, custom)
    2) Type of asset (RULE, NOTICE, etc.)
    3) Type of notification (executive actions, etc.)

  The Federal Register API allows us to specify date ranges using:
    conditions[publication_date][gte]=YYYY-MM-DD
    conditions[publication_date][lte]=YYYY-MM-DD

  We can also set the document type, e.g.:
    conditions[type][]=RULE
    conditions[type][]=NOTICE
    conditions[type][]=PRESDOCU (for Presidential Documents)

  For 'executive actions', we might try:
    conditions[presidential_document_type]=executive_order
  or other relevant params from the Federal Register docs.
*/

// We'll enhance fetchArticles to accept an object with optional parameters.

export async function fetchArticles(
  {
    searchTerm = '',
    pageNumber = 1,
    startDate = '', // YYYY-MM-DD
    endDate = '',   // YYYY-MM-DD
    types = [],     // array of doc types, e.g. ['RULE','NOTICE','PRESDOCU']
    presidentialAction = false // whether to include e.g. executive orders
  }
) {
  try {
    // If we have absolutely no search term or filters, let's not fetch anything.
    const hasSomeSearch = searchTerm || startDate || endDate || types.length > 0 || presidentialAction;
    if (!hasSomeSearch) {
      return { results: [] };
    }

    let url = `https://www.federalregister.gov/api/v1/articles?per_page=20&page=${pageNumber}`;

    // searchTerm
    if (searchTerm) {
      url += `&conditions[term]=${encodeURIComponent(searchTerm)}`;
    }

    // date range
    if (startDate) {
      url += `&conditions[publication_date][gte]=${startDate}`;
    }
    if (endDate) {
      url += `&conditions[publication_date][lte]=${endDate}`;
    }

    // doc types
    // e.g. conditions[type][]=RULE
    if (types.length > 0) {
      types.forEach((t) => {
        url += `&conditions[type][]=${encodeURIComponent(t)}`;
      });
    }

    // if user wants executive actions
    // e.g. conditions[presidential_document_type]=executive_order
    if (presidentialAction) {
      url += `&conditions[presidential_document_type]=executive_order`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch data from Federal Register');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

// existing fetchDocument remains the same
export async function fetchDocument(documentNumber) {
  if (!documentNumber) {
    throw new Error('No document number provided');
  }
  try {
    const url = `https://www.federalregister.gov/api/v1/documents/${documentNumber}`;
    const resp = await fetch(url);
    if (!resp.ok) {
      throw new Error(`Failed to fetch document #${documentNumber}`);
    }
    const data = await resp.json();
    return data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

export default function App() {
  // existing states
  const [searchTerm, setSearchTerm] = useState('');
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [sortOrder, setSortOrder] = useState('asc');
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedDocDetails, setSelectedDocDetails] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState(null);

  // NEW: states for time range
  const [timeRange, setTimeRange] = useState('any'); // 'any','today','yesterday','week','custom'
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // NEW: states for doc types
  // e.g. RULE, NOTICE, PRESDOCU (for presidential docs), PRORULE (proposed rule)
  const [selectedTypes, setSelectedTypes] = useState([]);

  // NEW: to track whether user wants executive actions
  const [executiveActions, setExecutiveActions] = useState(false);

  // build final date range from timeRange
  useEffect(() => {
    const today = new Date();
    const yyyy = today.getFullYear();
    let mm = (today.getMonth() + 1).toString().padStart(2, '0');
    let dd = today.getDate().toString().padStart(2, '0');
    const todayStr = `${yyyy}-${mm}-${dd}`;

    const yesterdayDate = new Date(today);
    yesterdayDate.setDate(yesterdayDate.getDate() - 1);
    const yy = yesterdayDate.getFullYear();
    let mm2 = (yesterdayDate.getMonth() + 1).toString().padStart(2, '0');
    let dd2 = yesterdayDate.getDate().toString().padStart(2, '0');
    const yesterdayStr = `${yy}-${mm2}-${dd2}`;

    if (timeRange === 'today') {
      setStartDate(todayStr);
      setEndDate(todayStr);
    } else if (timeRange === 'yesterday') {
      setStartDate(yesterdayStr);
      setEndDate(yesterdayStr);
    } else if (timeRange === 'week') {
      const weekAgo = new Date(today);
      weekAgo.setDate(weekAgo.getDate() - 7);
      const y2 = weekAgo.getFullYear();
      let m2 = (weekAgo.getMonth() + 1).toString().padStart(2, '0');
      let d2 = weekAgo.getDate().toString().padStart(2, '0');
      const weekAgoStr = `${y2}-${m2}-${d2}`;
      setStartDate(weekAgoStr);
      setEndDate(todayStr);
    } else if (timeRange === 'any') {
      setStartDate('');
      setEndDate('');
    } else if (timeRange === 'custom') {
      // do nothing, we let user set date pickers
    }
  }, [timeRange]);

  const loadArticles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchArticles({
        searchTerm,
        pageNumber: page,
        startDate,
        endDate,
        types: selectedTypes,
        presidentialAction: executiveActions,
      });

      if (page === 1) {
        setArticles(data.results || []);
      } else {
        setArticles((prev) => [...prev, ...(data.results || [])]);
      }
    } catch (error) {
      console.error('loadArticles error:', error);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, page, startDate, endDate, selectedTypes, executiveActions]);

  // reset page and reload whenever these fields change
  useEffect(() => {
    setPage(1);
    // If none of our fields are set, we can choose not to auto-load.
    // But let's go ahead and load if anything changed.
    loadArticles();
  }, [searchTerm, startDate, endDate, selectedTypes, executiveActions, loadArticles]);

  useEffect(() => {
    if (page > 1) {
      loadArticles();
    }
  }, [page, loadArticles]);

  const handleLoadMore = () => {
    if (!loading) {
      setPage((prevPage) => prevPage + 1);
    }
  };

  const handleSortByTitle = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    setSortOrder(newOrder);
    const sorted = [...articles].sort((a, b) => {
      if (!a.title) return 1;
      if (!b.title) return -1;
      if (newOrder === 'asc') {
        return a.title.localeCompare(b.title);
      } else {
        return b.title.localeCompare(a.title);
      }
    });
    setArticles(sorted);
  };

  const handleArticleClick = async (article) => {
    setSelectedArticle(article);
    setDocError(null);
    setSelectedDocDetails(null);

    if (article.document_number) {
      try {
        setDocLoading(true);
        const docData = await fetchDocument(article.document_number);
        setSelectedDocDetails(docData);
      } catch (err) {
        setDocError(err.message);
      } finally {
        setDocLoading(false);
      }
    }
  };

  const handleCloseDetail = () => {
    setSelectedArticle(null);
    setSelectedDocDetails(null);
    setDocError(null);
    setDocLoading(false);
  };

  // handle doc type toggle
  const handleTypeToggle = (typeVal) => {
    if (selectedTypes.includes(typeVal)) {
      setSelectedTypes(selectedTypes.filter((t) => t !== typeVal));
    } else {
      setSelectedTypes([...selectedTypes, typeVal]);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Federal Register Search</h1>

      {/* Search term input */}
      <div style={styles.searchContainer}>
        <input
          type="text"
          placeholder="Enter search term..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.input}
        />
        <button
          style={styles.searchButton}
          onClick={() => {
            setPage(1);
            setArticles([]);
            loadArticles();
          }}
        >
          Search
        </button>
      </div>

      {/* Time range selectors */}
      <div style={{ marginBottom: '8px' }}>
        <label>
          Time Range:{' '}
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="any">Any Time</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="week">This Week</option>
            <option value="custom">Custom Range</option>
          </select>
        </label>
        {timeRange === 'custom' && (
          <>
            <div>
              <label>
                Start Date:{' '}
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </label>
            </div>
            <div>
              <label>
                End Date:{' '}
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                />
              </label>
            </div>
          </>
        )}
      </div>

      {/* Document Type checkboxes */}
      <div style={{ marginBottom: '8px' }}>
        <p>Document Types (select any):</p>
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes('RULE')}
            onChange={() => handleTypeToggle('RULE')}
          />
          RULE
        </label>{' '}
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes('NOTICE')}
            onChange={() => handleTypeToggle('NOTICE')}
          />
          NOTICE
        </label>{' '}
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes('PRORULE')}
            onChange={() => handleTypeToggle('PRORULE')}
          />
          Proposed Rule
        </label>{' '}
        <label>
          <input
            type="checkbox"
            checked={selectedTypes.includes('PRESDOCU')}
            onChange={() => handleTypeToggle('PRESDOCU')}
          />
          Presidential Document
        </label>
      </div>

      {/* Executive actions switch */}
      <div style={{ marginBottom: '8px' }}>
        <label>
          <input
            type="checkbox"
            checked={executiveActions}
            onChange={() => setExecutiveActions(!executiveActions)}
          />
          Include Executive Actions (e.g., Executive Orders)
        </label>
      </div>

      <button style={styles.sortButton} onClick={handleSortByTitle}>
        Sort by Title ({sortOrder.toUpperCase()})
      </button>

      {loading && articles.length === 0 && (
        <p style={styles.loadingText}>Loading...</p>
      )}

      <div>
        {articles.map((item, index) => (
          <div
            key={item.id ? item.id : index}
            style={styles.articleContainer}
            onClick={() => handleArticleClick(item)}
          >
            <h2 style={styles.articleTitle}>{item.title}</h2>
            <p style={styles.articleDetails}>
              Agencies: {item.agencies?.map((a) => a.name).join(', ') || 'N/A'}
            </p>
            <p style={styles.articleDetails}>
              Published on: {item.publication_date}
            </p>
            {item.document_number && (
              <p style={styles.articleDetails}>
                Doc #: {item.document_number}
              </p>
            )}
          </div>
        ))}
      </div>

      {articles.length > 0 && !loading && (
        <button style={styles.loadMoreButton} onClick={handleLoadMore}>
          Load More
        </button>
      )}
      {loading && articles.length > 0 && (
        <p style={styles.loadingText}>Loading more...</p>
      )}

      {/* detail modal if selectedArticle is set */}
      {selectedArticle && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalContent}>
            <h2 style={styles.detailHeader}>{selectedArticle.title}</h2>
            <p><strong>Agencies:</strong> {selectedArticle.agencies?.map((a) => a.name).join(', ') || 'N/A'}</p>
            <p><strong>Publication Date:</strong> {selectedArticle.publication_date}</p>
            {selectedArticle.html_url && (
              <p>
                <strong>Federal Register Link:</strong>{' '}
                <a href={selectedArticle.html_url} target="_blank" rel="noopener noreferrer">
                  View on FederalRegister.gov
                </a>
              </p>
            )}
            {selectedArticle.docket_ids && selectedArticle.docket_ids.length > 0 && (
              <p><strong>Docket IDs:</strong> {selectedArticle.docket_ids.join(', ')}</p>
            )}
            {selectedArticle.document_number && (
              <p><strong>Document Number:</strong> {selectedArticle.document_number}</p>
            )}
            <hr style={{ margin: '16px 0' }} />
            {docLoading && <p>Loading Document...</p>}
            {docError && (
              <p style={{ color: 'red' }}>Error loading doc: {docError}</p>
            )}
            {selectedDocDetails && !docLoading && !docError && (
              <div>
                {selectedDocDetails.body_html && (
                  <div
                    style={{ border: '1px solid #ccc', padding: '8px', marginBottom: '8px', maxHeight: '400px', overflowY: 'scroll' }}
                    dangerouslySetInnerHTML={{ __html: selectedDocDetails.body_html }}
                  />
                )}
                {selectedDocDetails.pdf_url && (
                  <p>
                    <strong>PDF:</strong> <a href={selectedDocDetails.pdf_url} target="_blank" rel="noopener noreferrer">Open PDF</a>
                  </p>
                )}
              </div>
            )}
            <button style={styles.closeButton} onClick={handleCloseDetail}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Minimal inline style object
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '16px',
    backgroundColor: '#F5F5F5',
    minHeight: '100vh'
  },
  header: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '16px',
    textAlign: 'center',
  },
  searchContainer: {
    display: 'flex',
    flexDirection: 'row',
    marginBottom: '16px',
    alignItems: 'center',
    gap: '8px'
  },
  input: {
    flex: 1,
    padding: '8px',
    border: '1px solid #ccc',
    borderRadius: '4px'
  },
  searchButton: {
    padding: '8px 16px',
    backgroundColor: '#007AFF',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  sortButton: {
    padding: '10px 20px',
    backgroundColor: '#007AFF',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginBottom: '12px'
  },
  loadMoreButton: {
    padding: '10px 20px',
    backgroundColor: '#007AFF',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    marginTop: '12px'
  },
  articleContainer: {
    backgroundColor: '#fff',
    padding: '12px',
    marginBottom: '8px',
    borderRadius: '4px',
    cursor: 'pointer'
  },
  articleTitle: {
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '4px'
  },
  articleDetails: {
    fontSize: '14px',
    color: '#555'
  },
  loadingText: {
    textAlign: 'center',
    color: '#555',
    margin: '8px'
  },
  // modal styling
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999,
  },
  modalContent: {
    backgroundColor: '#fff',
    padding: '20px',
    borderRadius: '8px',
    maxWidth: '600px',
    width: '90%',
    boxShadow: '0 2px 8px rgba(0,0,0,0.25)'
  },
  detailHeader: {
    marginTop: 0,
    marginBottom: '16px',
    fontSize: '20px',
    fontWeight: 'bold'
  },
  closeButton: {
    marginTop: '16px',
    backgroundColor: '#007AFF',
    color: '#fff',
    border: 'none',
    padding: '8px 16px',
    borderRadius: '4px',
    cursor: 'pointer'
  }
};

/*
  Test Cases:
    1) fetchArticles('EPA', 1) -> returns an object containing a 'results' array.
    2) Sorting toggles from 'asc' to 'desc' and modifies 'articles' in the correct order.

  NOTE: The fetchArticles test requires network access. If you run tests offline, you must mock fetch.
*/

// existing testFetchArticles, testSorting, etc.
export async function testFetchArticles() {
  try {
    // We'll just do a basic search with minimal or default filters.
    const data = await fetchArticles({ searchTerm: 'EPA', pageNumber: 1 });
    if (!data.results) throw new Error("Expected 'results' array in returned data.");
    console.log('fetchArticles test passed:', data.results.length, 'article(s) fetched');
  } catch (err) {
    console.error('fetchArticles test failed:', err);
  }
}

export function testSorting() {
  const mockArticles = [
    { title: 'Z Title' },
    { title: 'A Title' },
    { title: 'M Title' },
  ];

  // Asc sort
  const ascSorted = [...mockArticles].sort((a, b) => a.title.localeCompare(b.title));
  if (ascSorted[0].title !== 'A Title') {
    throw new Error('Asc sort test failed');
  }

  // Desc sort
  const descSorted = [...mockArticles].sort((a, b) => b.title.localeCompare(a.title));
  if (descSorted[0].title !== 'Z Title') {
    throw new Error('Desc sort test failed');
  }

  console.log('testSorting passed');
}

export async function testNoSearchTerm() {
  try {
    const data = await fetchArticles({}); // no searchTerm, no filters.
    if (!data.results || data.results.length !== 0) {
      throw new Error('Expected an empty array when no filters or searchTerm');
    }
    console.log('testNoSearchTerm passed');
  } catch (err) {
    console.error('testNoSearchTerm failed:', err);
  }
}

export async function testFetchDocument() {
  try {
    // Random known doc number. Might fail if doc no longer exists.
    const docNumber = '2023-01150';
    const docData = await fetchDocument(docNumber);
    if (!docData.title) {
      throw new Error('Expected the doc to have a title');
    }
    console.log('fetchDocument test passed:', docData.title);
  } catch (err) {
    console.error('fetchDocument test failed:', err);
  }
}

// NEW TEST: advanced filters
export async function testAdvancedFilters() {
  try {
    // For example, search for 'EPA' in the last week, specifically RULE type.
    const data = await fetchArticles({
      searchTerm: 'EPA',
      startDate: '2025-01-20',
      endDate: '2025-01-27',
      types: ['RULE'],
      pageNumber: 1,
    });
    // We cannot guarantee results exist, but we can at least check data.results is an array.
    if (!data.results) {
      throw new Error('Expected a results array for advanced filter test');
    }
    console.log('testAdvancedFilters passed:', data.results.length, 'article(s)');
  } catch (err) {
    console.error('testAdvancedFilters failed:', err);
  }
}
