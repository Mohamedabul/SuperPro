import { useState } from 'react'
import { 
  Box, 
  Button, 
  Container, 
  Paper, 
  Typography,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  useTheme,
  useMediaQuery,
  LinearProgress,
  CssBaseline,
  Tab,
  Tabs
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import {
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  TableChart as TableChartIcon,
  GridOn as GridOnIcon
} from '@mui/icons-material'
import axios from 'axios'

function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState(0)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0]
    setFile(selectedFile)
    setError(null)
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post('http://localhost:5000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      setAnalysis(response.data.analysis)
    } catch (err) {
      setError(err.response?.data?.error || 'An error occurred while uploading the file')
    } finally {
      setLoading(false)
    }
  }

  const getGridColumns = () => {
    if (!analysis || !analysis.columns) return []
    return analysis.columns.map(column => ({
      field: column,
      headerName: column,
      flex: 1,
      minWidth: 150,
      renderCell: (params) => {
        const isMissing = analysis.missing_positions[column].includes(params.row.id - 1)
        const isTBD = analysis.tbd_positions[column].includes(params.row.id - 1)
        const value = params.value || '—'
        
        return (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              backgroundColor: isTBD 
                ? 'rgba(255, 165, 0, 0.1)'  // Orange background for TBD
                : isMissing 
                  ? 'rgba(255, 0, 0, 0.1)'   // Red background for missing
                  : 'transparent',
              color: isTBD ? 'orange' : 'inherit',
              fontStyle: isTBD ? 'italic' : 'normal',
              p: 1
            }}
          >
            {value}
          </Box>
        )
      }
    }))
  }

  const getGridRows = () => {
    if (!analysis || !analysis.data) return []
    return analysis.data.map((row, index) => ({
      id: index + 1,
      ...row
    }))
  }

  return (
    <>
      <CssBaseline />
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          width: '100vw',
          bgcolor: theme.palette.grey[100],
          overflowX: 'hidden'
        }}
      >
        <Container 
          maxWidth={false} 
          sx={{ 
            flex: 1,
            py: 4,
            px: { xs: 2, sm: 4, md: 6 }
          }}
        >
          <Grid container spacing={3}>
            {/* Header */}
            <Grid item xs={12}>
              <Card 
                elevation={3}
                sx={{
                  background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.dark} 90%)`,
                  color: 'white'
                }}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <AssessmentIcon sx={{ fontSize: 48, color: 'white', mb: 2 }} />
                  <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
                    Data Analysis Dashboard
                  </Typography>
                  <Typography variant="subtitle1" sx={{ color: 'rgba(255, 255, 255, 0.9)' }}>
                    Upload your CSV or Excel file for instant analysis
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* File Upload Section */}
            <Grid item xs={12}>
              <Card elevation={3}>
                <CardContent sx={{ p: 3 }}>
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: isMobile ? 'column' : 'row', 
                    alignItems: 'center', 
                    gap: 2,
                    width: '100%'
                  }}>
                    <input
                      accept=".csv,.xlsx,.xls"
                      style={{ display: 'none' }}
                      id="file-upload"
                      type="file"
                      onChange={handleFileChange}
                    />
                    <label htmlFor="file-upload">
                      <Button
                        variant="contained"
                        component="span"
                        startIcon={<CloudUploadIcon />}
                        sx={{ 
                          minWidth: '200px',
                          bgcolor: theme.palette.primary.main,
                          '&:hover': {
                            bgcolor: theme.palette.primary.dark,
                          }
                        }}
                      >
                        Choose File
                      </Button>
                    </label>
                    {file && (
                      <Typography sx={{ 
                        flex: 1, 
                        textAlign: isMobile ? 'center' : 'left',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        Selected: {file.name}
                      </Typography>
                    )}
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={handleUpload}
                      disabled={!file || loading}
                      startIcon={<TableChartIcon />}
                      sx={{ minWidth: '200px' }}
                    >
                      Analyze Data
                    </Button>
                  </Box>
                </CardContent>
                {loading && <LinearProgress />}
              </Card>
            </Grid>

            {/* Error Display */}
            {error && (
              <Grid item xs={12}>
                <Card sx={{ bgcolor: theme.palette.error.light }}>
                  <CardContent>
                    <Typography color="error" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {error}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Analysis Results */}
            {analysis && (
              <>
                <Grid item xs={12}>
                  <Card elevation={3}>
                    <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                      <Tabs 
                        value={activeTab} 
                        onChange={(e, newValue) => setActiveTab(newValue)}
                        variant="fullWidth"
                      >
                        <Tab 
                          icon={<AssessmentIcon />} 
                          label="Analysis" 
                          iconPosition="start"
                        />
                        <Tab 
                          icon={<GridOnIcon />} 
                          label="Data Grid" 
                          iconPosition="start"
                        />
                      </Tabs>
                    </Box>
                    {activeTab === 0 ? (
                      <CardContent>
                        <Grid container spacing={2} sx={{ mb: 3 }}>
                          <Grid item xs={12} sm={6}>
                            <Card variant="outlined">
                              <CardContent>
                                <Typography variant="h6" color="primary" gutterBottom>
                                  Total Rows
                                </Typography>
                                <Typography variant="h4">
                                  {analysis.total_rows}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                          <Grid item xs={12} sm={6}>
                            <Card variant="outlined">
                              <CardContent>
                                <Typography variant="h6" color="primary" gutterBottom>
                                  Total Columns
                                </Typography>
                                <Typography variant="h4">
                                  {analysis.total_columns}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        </Grid>

                        <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2 }}>
                          Missing Values Analysis
                        </Typography>
                        
                        <Box sx={{ width: '100%', overflow: 'auto' }}>
                          <Grid container spacing={2}>
                            {analysis.columns.map((column) => (
                              <Grid item xs={12} md={6} key={column}>
                                <Card variant="outlined">
                                  <CardContent>
                                    <Typography variant="subtitle1" color="primary" gutterBottom>
                                      {column}
                                    </Typography>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                                      <Typography variant="body2" color="text.secondary">
                                        Missing: {analysis.missing_values[column]}
                                      </Typography>
                                      <Typography variant="body2" sx={{ color: 'orange' }}>
                                        TBD: {analysis.tbd_values[column]}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        Type: {analysis.data_types[column]}
                                      </Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                      <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Missing Values:
                                      </Typography>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <LinearProgress 
                                          variant="determinate" 
                                          value={analysis.missing_percentage[column]} 
                                          sx={{ 
                                            flexGrow: 1,
                                            backgroundColor: 'rgba(255, 0, 0, 0.1)',
                                            '& .MuiLinearProgress-bar': {
                                              backgroundColor: 'rgba(255, 0, 0, 0.7)'
                                            }
                                          }}
                                        />
                                        <Typography variant="body2" color="text.secondary">
                                          {analysis.missing_percentage[column].toFixed(1)}%
                                        </Typography>
                                      </Box>
                                    </Box>
                                    <Box>
                                      <Typography variant="body2" color="text.secondary" gutterBottom>
                                        TBD Values:
                                      </Typography>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <LinearProgress 
                                          variant="determinate" 
                                          value={analysis.tbd_percentage[column]} 
                                          sx={{ 
                                            flexGrow: 1,
                                            backgroundColor: 'rgba(255, 165, 0, 0.1)',
                                            '& .MuiLinearProgress-bar': {
                                              backgroundColor: 'rgba(255, 165, 0, 0.7)'
                                            }
                                          }}
                                        />
                                        <Typography variant="body2" color="text.secondary">
                                          {analysis.tbd_percentage[column].toFixed(1)}%
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </CardContent>
                                </Card>
                              </Grid>
                            ))}
                          </Grid>
                        </Box>
                      </CardContent>
                    ) : (
                      <Box sx={{ height: 600, width: '100%', p: 2 }}>
                        <DataGrid
                          rows={getGridRows()}
                          columns={getGridColumns()}
                          pageSize={10}
                          rowsPerPageOptions={[10, 25, 50, 100]}
                          disableSelectionOnClick
                          density="comfortable"
                          sx={{
                            '& .MuiDataGrid-cell': {
                              padding: 0
                            }
                          }}
                        />
                      </Box>
                    )}
                  </Card>
                </Grid>
              </>
            )}
          </Grid>
        </Container>
      </Box>
    </>
  )
}

export default App
