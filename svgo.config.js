module.exports = {
  plugins: [
    'preset-default',
    {
      name: 'removeComments',
      active: true
    },
    {
      name: 'removeMetadata',
      active: true
    },
    {
      name: 'cleanupNumericValues',
      params: {
        floatPrecision: 2
      }
    },
    {
      name: 'convertPathData',
      params: {
        floatPrecision: 2
      }
    },
    {
      name: 'removeViewBox',
      active: false
    }
  ]
};