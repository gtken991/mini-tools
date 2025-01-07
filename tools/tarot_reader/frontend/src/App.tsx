import React, { useState } from 'react'
import {
  Box,
  Container,
  VStack,
  Heading,
  FormControl,
  FormLabel,
  Textarea,
  Select,
  Button,
  Grid,
  Text,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
} from '@chakra-ui/react'
import { useImagePreload } from './hooks/useImagePreload'
import { TarotCard } from './components/TarotCard'
import { doReading, ReadingResult } from './api/tarot'

const App: React.FC = () => {
  const [question, setQuestion] = useState('')
  const [spreadType, setSpreadType] = useState('single_card')
  const [result, setResult] = useState<ReadingResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { isComplete: imagesLoaded, hasErrors: imageErrors } = useImagePreload()

  const bgGradient = useColorModeValue(
    'linear(to-br, gray.800, purple.900)',
    'linear(to-br, gray.900, purple.900)'
  )
  const cardBg = useColorModeValue('whiteAlpha.200', 'whiteAlpha.100')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    try {
      const readingResult = await doReading(question, spreadType)
      setResult(readingResult)
    } catch (err) {
      setError(err instanceof Error ? err.message : '解读过程出错')
    } finally {
      setIsLoading(false)
    }
  }

  if (!imagesLoaded) {
    return (
      <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" bgGradient={bgGradient}>
        <VStack spacing={4}>
          <Box className="loading-spinner" />
          <Text color="white">正在加载塔罗牌图片...</Text>
        </VStack>
      </Box>
    )
  }

  if (imageErrors) {
    return (
      <Box minH="100vh" display="flex" alignItems="center" justifyContent="center" bgGradient={bgGradient}>
        <Alert
          status="error"
          variant="subtle"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          height="200px"
          bg="whiteAlpha.200"
          color="white"
        >
          <AlertIcon boxSize="40px" mr={0} />
          <AlertTitle mt={4} mb={1} fontSize="lg">
            图片加载出错
          </AlertTitle>
          <AlertDescription maxWidth="sm">
            无法加载塔罗牌图片，请刷新页面重试
          </AlertDescription>
        </Alert>
      </Box>
    )
  }

  return (
    <Box minH="100vh" bgGradient={bgGradient} py={4}>
      <Container maxW="container.lg">
        <VStack spacing={8} bg={cardBg} borderRadius="xl" p={6} boxShadow="xl">
          <Heading
            as="h1"
            size="xl"
            bgGradient="linear(to-r, cyan.400, purple.500)"
            bgClip="text"
            letterSpacing="tight"
          >
            塔罗牌解读
          </Heading>

          <Box as="form" onSubmit={handleSubmit} width="100%" maxW="md">
            <VStack spacing={6} align="stretch">
              <FormControl isRequired>
                <FormLabel color="white">你的问题</FormLabel>
                <Textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="请输入你想要解答的问题..."
                  bg="whiteAlpha.100"
                  border="1px solid"
                  borderColor="whiteAlpha.300"
                  _hover={{ borderColor: 'blue.400' }}
                  _focus={{ borderColor: 'blue.500', boxShadow: 'outline' }}
                  height="100px"
                  color="white"
                />
              </FormControl>

              <FormControl>
                <FormLabel color="white">选择牌阵</FormLabel>
                <Select
                  value={spreadType}
                  onChange={(e) => setSpreadType(e.target.value)}
                  bg="whiteAlpha.100"
                  border="1px solid"
                  borderColor="whiteAlpha.300"
                  color="white"
                  _hover={{ borderColor: 'blue.400' }}
                  _focus={{ borderColor: 'blue.500', boxShadow: 'outline' }}
                >
                  <option value="single_card">单张牌</option>
                  <option value="three_card">三张牌</option>
                  <option value="celtic_cross">凯尔特十字</option>
                </Select>
              </FormControl>

              <Button
                type="submit"
                colorScheme="blue"
                size="lg"
                width="100%"
                isLoading={isLoading}
                loadingText="解读中..."
                disabled={!question.trim()}
              >
                开始解读
              </Button>
            </VStack>
          </Box>

          {error && (
            <Alert
              status="error"
              variant="subtle"
              bg="whiteAlpha.200"
              color="white"
              borderRadius="md"
            >
              <AlertIcon />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <VStack spacing={8} width="100%">
              <Grid
                templateColumns={`repeat(auto-fit, minmax(180px, 1fr))`}
                gap={6}
                width="100%"
                bg="whiteAlpha.100"
                p={6}
                borderRadius="xl"
              >
                {result.cards.map((card) => (
                  <TarotCard
                    key={card.id}
                    card={card}
                    isImageLoaded={imagesLoaded}
                  />
                ))}
              </Grid>

              <Box
                width="100%"
                bg="whiteAlpha.200"
                p={6}
                borderRadius="xl"
                color="white"
              >
                <Heading
                  as="h2"
                  size="lg"
                  mb={4}
                  bgGradient="linear(to-r, cyan.400, purple.500)"
                  bgClip="text"
                >
                  解读结果
                </Heading>
                <Text
                  whiteSpace="pre-line"
                  fontSize="lg"
                  sx={{
                    '& > p': {
                      mb: 4,
                      bg: 'whiteAlpha.100',
                      p: 4,
                      borderRadius: 'md',
                    },
                  }}
                >
                  {result.result}
                </Text>
              </Box>
            </VStack>
          )}
        </VStack>
      </Container>
    </Box>
  )
}

export default App
