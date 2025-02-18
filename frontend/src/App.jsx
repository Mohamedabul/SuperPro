import { useState } from 'react'
import { PaginationProvider, usePagination } from './contexts/PaginationContext'
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
  Tabs,
  Tooltip
} 
from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import {
  CloudUpload as CloudUploadIcon,
  Assessment as AssessmentIcon,
  TableChart as TableChartIcon,
  GridOn as GridOnIcon,
  FileDownload as FileDownloadIcon
} from '@mui/icons-material'
import axios from 'axios'
import ExcelJS from 'exceljs'
 
function AppContent() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState(0)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const { page, setPage, rowsPerPage } = usePagination()


 
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0]
    setFile(selectedFile)
    setError(null)
  }
  const getPaginatedData = () => {
    if (!analysis || !analysis.data) return [];
    const startIndex = page * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    return analysis.data
      .slice(startIndex, endIndex)
      .map((row, index) => ({
        id: startIndex + index + 1,
        ...row
      }));
  };


  const handleExport = async () => {
    try {
      console.log('Export started')
      const headers = analysis.columns
      const rows = analysis.data
     
      const workbook = new ExcelJS.Workbook()
      const worksheet = workbook.addWorksheet('Data Analysis')
     
      // Define columns with headers
      worksheet.columns = headers.map(header => ({
        header: header,
        key: header,
        width: 15
      }))
     
      // Add data rows
      rows.forEach((row, rowIndex) => {
        const rowData = {}
        headers.forEach(header => {
          rowData[header] = row[header] ?? ''
        })
        worksheet.addRow(rowData)
       
        // Apply cell styling
        headers.forEach((header, colIndex) => {
          const cell = worksheet.getCell(rowIndex + 2, colIndex + 1)
          const value = row[header]
          const isMissing = analysis.missing_positions[header].includes(rowIndex)
          const isTBD = analysis.tbd_positions[header].includes(rowIndex)
          const hasDelimiter = analysis.delimiter_analysis[header]?.includes(rowIndex)
          const hasRegionMismatch = header === analysis.regional_column && analysis.region_mismatches?.includes(rowIndex)
          const hasLocationMismatch = header === analysis.location_column && analysis.location_mismatch?.includes(rowIndex)
          const isDuplicate = analysis.duplicate_rows.indices.includes(rowIndex)
         
          // Add check for uppercase, excluding regional column and integers
          const isUpperCase = header !== analysis.regional_column && header !== analysis.location_column &&
                   typeof value === 'string' &&
                   value === value.toUpperCase() &&
                   value.length > 1 &&
                   isNaN(value) &&
                   !value.match(/^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}/) &&
                   !value.match(/^(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}$/) &&
                   !value.match(/^(19|20)\d{2}[\/\-](0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])$/)
  
          // Apply fill colors based on conditions
          if (isDuplicate) {
            cell.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: 'FFFFE6FF' }  // Light pink for duplicates
            }
          } else if (hasRegionMismatch || hasLocationMismatch) {
            cell.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: 'FFFFE6E6' }  // Light red for mismatches
            }
          } else if (hasDelimiter) {
            cell.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: 'FFFFE6E6' }  // Light red for delimiter errors
            }
          } else if (isTBD || isMissing || isUpperCase) {
            cell.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: 'FFFFE6CC' }  // Light orange for TBD/missing/uppercase
            }
          }
        })
      })
     
      // Make header row bold
      worksheet.getRow(1).font = { bold: true }
     
      // Generate buffer and create download
      const buffer = await workbook.xlsx.writeBuffer()
      const blob = new Blob([buffer], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
     
      // Create and trigger download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `data_analysis_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
     
      // Cleanup
      setTimeout(() => {
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      }, 0)
     
      console.log('Export completed')
    } catch (error) {
      console.error('Export failed:', error)
      setError('Failed to export data. Please try again.')
    }
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
      maxWidth: 300,
      resizable: true,
      headerClassName: 'bold-header',
 
      renderCell: (params) => {
        const isMissing = analysis.missing_positions[column].includes(params.row.id - 1)
        const isTBD = analysis.tbd_positions[column].includes(params.row.id - 1)
        const isDuplicate = analysis.duplicate_rows.indices.includes(params.row.id - 1)
        const hasDelimiter = analysis.delimiter_analysis[column]?.includes(params.row.id - 1)
        const hasRegionMismatch = column === analysis.regional_column && analysis.region_mismatches?.includes(params.row.id - 1)
        const hasLocationMismatch = column === analysis.location_column && analysis.location_mismatch?.includes(params.row.id - 1)
        const value = params.value
       
        // Add check for uppercase, excluding regional column
        const isUpperCase = column !== analysis.regional_column && column !== analysis.location_column &&
                   typeof value === 'string' &&
                   value === value.toUpperCase() &&
                   value.length > 1 &&
                   isNaN(value) &&
                   !value.match(/^\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}/) &&
                   !value.match(/^(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}$/) &&
                   !value.match(/^(19|20)\d{2}[\/\-](0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])$/) && value !== 'EMEA' &&
                   value !== 'APAC' &&
                   value !== 'EMEA/APAC' &&
                   value !== 'APAC/EMEA' &&
                   value !== 'EMEA, APAC' &&
                   value !== 'US' && value !== 'UK'

 
                   let tooltipMessage = [];
                   const formatMessage = (message) => {
                     const parts = message.split(": ");
                     return parts.length > 1 ? (
                       <span>
                         <strong>{parts[0]}:</strong> {parts[1]}
                       </span>
                     ) : (
                       message
                     );
                   };
            
                   if (hasLocationMismatch)
                     tooltipMessage.push(
                       formatMessage("Location Mismatch: Regional value doesn't match with location")
                     );
                   if (hasRegionMismatch)
                     tooltipMessage.push(
                       formatMessage("Region Mismatch: Location value doesn't match with region")
                     );
                   if (hasDelimiter)
                     tooltipMessage.push(
                       formatMessage("Delimiter Error: This delimiter is not allowed in this column")
                     );
                   if (isTBD)
                     tooltipMessage.push(
                       formatMessage("TBD Value: Cell contains a TBD or placeholder or '-' or NUll or None value")
                     );
                   if (isMissing)
                     tooltipMessage.push(
                       formatMessage("Missing Value: Cell contains missing")
                     );
                   if (isDuplicate)
                     tooltipMessage.push(
                       formatMessage("Duplicate Row: This row is a duplicate of another row in the dataset")
                     );
                   if (isUpperCase)
                     tooltipMessage.push(
                       formatMessage("Uppercase Warning: Cell contains all uppercase text")
                     );

        const content = (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              boxSizing: 'border-box',
              gap: 0,
              backgroundColor: hasRegionMismatch || hasLocationMismatch
                ? 'rgba(255, 0, 0, 0.1)'  
                : hasDelimiter
                  ? 'rgba(255, 0, 0, 0.1)'  
                  : isTBD
                    ? 'rgba(255, 165, 0, 0.1)'  
                    : isMissing
                      ? 'rgba(255, 165, 0, 0.1)'
                      : isUpperCase
                        ? 'rgba(255, 165, 0, 0.1)'  // Light purple for uppercase
                        : 'transparent',
              color: isTBD ? 'orange' : 'inherit',
              fontStyle: isTBD ? 'italic' : 'normal',
              p: 1,
              whiteSpace: 'normal',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              minWidth: 0
            }}
          >
            {value}
          </Box>
        )
       
        return tooltipMessage.length > 0 ? (
          <Tooltip
            title={
              <div>
                {tooltipMessage.map((msg, index) => (
                  <div key={index}>{msg}</div>
                ))}
              </div>
            }
            arrow
            placement="top"
            sx={{ width: '100%', height: '100%' }}
          >
            {content}
          </Tooltip>
        ) : (
          content
        );
      },
    }));
  };
 
 
  // const getPaginatedData = () => {
  //   if (!analysis || !analysis.data) return [];
  //   const startIndex = page * rowsPerPage;
  //   const endIndex = startIndex + rowsPerPage;
  //   return analysis.data
  //     .slice(startIndex, endIndex)
  //     .map((row, index) => ({
  //       id: startIndex + index + 1,
  //       ...row
  //     }));
  // };
 
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
                          <Grid item xs={12} sm={6} md={4}>
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
                          <Grid item xs={12} sm={6} md={4}>
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
                          <Grid item xs={12} sm={6} md={4}>
                            <Card variant="outlined">
                              <CardContent>
                                <Typography variant="h6" color="primary" gutterBottom>
                                  Duplicate Rows
                                </Typography>
                                <Typography variant="h4">
                                  {analysis.duplicate_rows.total}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {analysis.duplicate_rows.percentage.toFixed(1)}% of total rows
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        </Grid>
 
                        <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2 }}>
                          Column Analysis
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
                      <Box sx={{ height: 1000, width: '100%', p: 2 }}>
                        <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, bgcolor: 'rgba(255, 0, 0, 0.1)' }} />
                              <Typography variant="body2"><b>Location / Regional Mismatch /Delimiter</b></Typography>
                            </Box>
                            {/* <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, bgcolor: 'rgba(0, 128, 0, 0.1)' }} />
                              <Typography variant="body2"><b>Delimiter Mismatch</b></Typography>
                            </Box> */}
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, bgcolor: 'rgba(255, 165, 0, 0.1)' }} />
                              <Typography variant="body2"><b>Missing/TBD Value/UpperCase Text</b></Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, bgcolor: 'rgba(255, 0, 255, 0.1)' }} />
                              <Typography variant="body2"><b>Duplicate Row</b></Typography>
                            </Box>
                            {/* <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ width: 20, height: 20, bgcolor: 'rgba(147, 112, 219, 0.1)' }} />
                              <Typography variant="body2"><b>Uppercase Text</b></Typography>
                            </Box> */}
                            <Button
                              variant="contained"
                              color="primary"
                              onClick={handleExport}
                              startIcon={<FileDownloadIcon />}
                              disabled={!analysis}
                            >
                              Export Data
                            </Button>
                          </Box>
 
                        <DataGrid
                            rows={getPaginatedData()}
                            columns={getGridColumns()}
                            pageSize={rowsPerPage}
                            rowsPerPageOptions={[rowsPerPage]}
                            pagination
                            paginationMode="server"
                            onPageChange={(newPage) => setPage(newPage)}
                            page={page}
                            rowCount={analysis?.data?.length || 0}
                            loading={loading}
                            disableSelectionOnClick
                            density="comfortable"
                            components={{
                            Pagination: () => (
                              <Box sx={{ 
                                position: 'fixed',
                                bottom: 20,
                                left: '50%',
                                transform: 'translateX(-50%)',
                                display: 'flex',
                                justifyContent: 'center',
                                backgroundColor: 'white',
                                padding: '10px 20px',
                                borderRadius: '8px',
                                boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
                                zIndex: 9999
                              }}>
                              <Button 
                                onClick={() => setPage(Math.max(0, page - 1))}
                                disabled={page === 0}
                                sx={{ mr: 2 }}
                                variant="contained"
                              >
                                Previous
                              </Button>
                              <Typography sx={{ mx: 2, alignSelf: 'center' }}>
                                Page {page + 1} of {Math.ceil((analysis?.data?.length || 0) / rowsPerPage)}
                              </Typography>
                              <Button 
                                  onClick={() => setPage(page + 1)}
                                  disabled={!analysis?.data || (page + 1) * rowsPerPage >= analysis.data.length}
                                  variant="contained"
                                >
                                Next
                              </Button>
                              </Box>
                            )
                            }}
                          getRowClassName={(params) => {
                            const isDuplicate = analysis.duplicate_rows.indices.includes(params.row.id - 1)
                            return isDuplicate ? 'duplicate-row' : ''
                          }}
                          sx={{
                            '& .MuiDataGrid-cell': {
                              padding: 0
                            },
                            '& .duplicate-row': {
                              backgroundColor: 'rgba(255, 0, 255, 0.1)',  
                              '&:hover': {
                                backgroundColor: 'rgba(255, 0, 255, 0.2)',  
                              }
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
 
function App() {
  return (
    <PaginationProvider>
      <AppContent />
    </PaginationProvider>
  )
}

export default App