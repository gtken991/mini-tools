import styled from '@emotion/styled'

export const CardContainer = styled.div`
  position: relative;
  width: 200px;
  height: 300px;
  perspective: 1000px;
`

export const CardInner = styled.div<{ isFlipped: boolean }>`
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.8s;
  transform-style: preserve-3d;
  transform: ${props => props.isFlipped ? 'rotateY(180deg)' : 'none'};
` 