import React from 'react';

export const EXAMPLE_QUERIES = [
  {
    category: 'Objects',
    queries: [
      'handbag',
      'cell phone',
      'person',
      'bicycle'
    ]
  },
  {
    category: 'Attributes',
    queries: [
      'person with white shirt',
      'person wearing black shoes',
      'person with glasses',
      'person wearing a hat',
      'person with long hair',
      'person carrying a backpack',
      'person wearing a necklace',
      'person with blue jeans',
      'person wearing white sneakers'
    ]
  },
  {
    category: 'Relations',
    queries: [
      'person riding bicycle',
      'person near another person'
    ]
  },
  {
    category: 'Speech',
    queries: [
      'what they say: "what\'s up"',
      'what they say: "okay"'
    ]
  }
];

export const ExampleQueries = ({ activeQuery, onSelectQuery }) => {
  return (
    <div className="example-queries-section">
      <div className="example-queries-title">
        <span>Try Example Queries</span>
      </div>
      <div className="example-queries-categories">
        {EXAMPLE_QUERIES.map((cat) => (
          <div key={cat.category} className="query-category-group">
            <span className="category-label">{cat.category}</span>
            <div className="chips-list">
              {cat.queries.map((qText) => (
                <button
                  key={qText}
                  type="button"
                  className={`query-chip ${activeQuery === qText ? 'active' : ''}`}
                  onClick={() => onSelectQuery(qText)}
                >
                  {qText}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ExampleQueries;
