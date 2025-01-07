import React, { Component, ErrorInfo, ReactNode } from 'react'
import { Box, Heading, Text, Button } from '@chakra-ui/react'

interface Props {
    children: ReactNode
}

interface State {
    hasError: boolean
    error?: Error
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    }

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error }
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('错误详情:', error, errorInfo)
    }

    private handleRetry = () => {
        window.location.reload()
    }

    public render() {
        if (this.state.hasError) {
            return (
                <Box
                    minH="100vh"
                    display="flex"
                    flexDirection="column"
                    alignItems="center"
                    justifyContent="center"
                    bg="gray.900"
                    color="white"
                    p={6}
                    textAlign="center"
                >
                    <Heading mb={4} size="xl">
                        抱歉，出现了一些问题
                    </Heading>
                    <Text mb={6} fontSize="lg">
                        请刷新页面重试
                    </Text>
                    <Button
                        colorScheme="blue"
                        size="lg"
                        onClick={this.handleRetry}
                    >
                        刷新页面
                    </Button>
                </Box>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary 