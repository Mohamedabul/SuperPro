import React, { createContext, useContext, useState } from 'react';

const PaginationContext = createContext();

export const usePagination = () => {
	const context = useContext(PaginationContext);
	if (!context) {
		throw new Error('usePagination must be used within a PaginationProvider');
	}
	return context;
};

export const PaginationProvider = ({ children }) => {
	const [page, setPage] = useState(0);
	const rowsPerPage = 100;

	const handlePageChange = (newPage) => {
		setPage(newPage);
	};

	return (
		<PaginationContext.Provider
			value={{
				page,
				setPage,
				rowsPerPage,
				handlePageChange,
			}}
		>
			{children}
		</PaginationContext.Provider>
	);
};