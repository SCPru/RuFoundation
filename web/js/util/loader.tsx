import * as React from 'react';
import styled from 'styled-components';


interface Props {
    size?: number
    borderSize?: number
    color?: string
    className? : string
}


const LoaderStyle = styled.div<Props>`
@keyframes ldio-rmqiozoxwgk {
  0% { transform: translate(-50%,-50%) rotate(0deg); }
  100% { transform: translate(-50%,-50%) rotate(360deg); }
}

width: ${props => props.size}px;
height: ${props => props.size}px;
display: inline-block;
overflow: hidden;

.ldio {
    width: 100%;
    height: 100%;
    position: relative;
    transform: translateZ(0) scale(1);
    backface-visibility: hidden;
    transform-origin: 0 0; /* see note above */
    div {
      box-sizing: content-box;
      animation: ldio-rmqiozoxwgk 1s linear infinite;
      top: ${props => props.size/2}px;
      left: ${props => props.size/2}px;
      position: absolute;
      width: ${props => props.size - props.borderSize*2}px;
      height: ${props => props.size - props.borderSize*2}px;
      border: ${props => props.borderSize}px solid ${props => props.color};
      border-top-color: transparent;
      border-radius: 50%;
    }
}
`;



const Loader: React.FC<Props> = ({ className, size, borderSize, color }) =>{
    return (
        <LoaderStyle className={className} size={size || 32} borderSize={borderSize || 4} color={color || '#e15b64'}>
            <div className="ldio">
                <div/>
            </div>
        </LoaderStyle>
    )
}


export default Loader
