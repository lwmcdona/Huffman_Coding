# The functions in this file are to be implemented by students.

import bitio
import huffman


def read_tree (bitreader):
    '''Read a description of a Huffman tree from the given bit reader,
    and construct and return the tree. When this function returns, the
    bit reader should be ready to read the next bit immediately
    following the tree description.

    Huffman trees are stored in the following format:
      * TreeLeafEndMessage is represented by the two bits 00.
      * TreeLeaf is represented by the two bits 01, followed by 8 bits
          for the symbol at that leaf.
      * TreeBranch is represented by the single bit 1, followed by a
          description of the left subtree and then the right subtree.

    Args:
      bitreader: An instance of bitio.BitReader to read the tree from.

    Returns:
      A Huffman tree constructed according to the given description.
    '''
    bit = bitreader.readbit()
    # if the the first bit is 0, need to read the next bit
    if bit == 0:
        bit = bitreader.readbit()
        if bit == 1:
            # if the combination is 01, create a leaf with the next byte
            byte = bitreader.readbits(8)
            tree = huffman.TreeLeaf(byte)
        else:
            # if the combination is 00, create an end message
            tree = huffman.TreeLeafEndMessage()

    else:# if the first bit is 1, create a branch and recurse on the left side
         # then the right side
        tree = huffman.TreeBranch(read_tree(bitreader), read_tree(bitreader))

    return tree

def decompress (compressed, uncompressed):
    '''First, read a Huffman tree from the 'compressed' stream using your
    read_tree function. Then use that tree to decode the rest of the
    stream and write the resulting symbols to the 'uncompressed'
    stream.

    Args:
      compressed: A file stream from which compressed input is read.
      uncompressed: A writable file stream to which the uncompressed
          output is written.

    '''
    bitreader = bitio.BitReader(compressed)
    tree = read_tree(bitreader)
    message = list() # the list of ascii codes to be added to
    while True:
        char = huffman.decode(tree, bitreader) # decode the character
        if char == None: # if it's an endmessage, add to the list, exit
            break
        message.append(char) # otherwise add to the list
    # writes the message to the writable file stream

    uncompressed.write(bytes(message))


def write_tree (tree, bitwriter):
    '''Write the specified Huffman tree to the given bit writer.  The
    tree is written in the format described above for the read_tree
    function.

    DO NOT flush the bit writer after writing the tree.

    Args:
      tree: A Huffman tree.
      bitwriter: An instance of bitio.BitWriter to write the tree to.
    '''
    # if the tree is an EndMessage, write 00
    if isinstance(tree, huffman.TreeLeafEndMessage):
        bitwriter.writebits(0,2)
    # if the tree is a TreeLeaf, write 01, followed by the value in binary
    elif isinstance(tree, huffman.TreeLeaf):
        bitwriter.writebits(1,2)
        bitwriter.writebits(tree.value,8)
    # if the tree is a branch, write 1, and then write out each branch, left first
    elif isinstance(tree, huffman.TreeBranch):
        bitwriter.writebit(1)
        write_tree(tree.left, bitwriter)
        write_tree(tree.right, bitwriter)

def compress (tree, uncompressed, compressed):
    '''First write the given tree to the stream 'compressed' using the
    write_tree function. Then use the same tree to encode the data
    from the input stream 'uncompressed' and write it to 'compressed'.
    If there are any partially-written bytes remaining at the end,
    write 0 bits to form a complete byte.

    Args:
      tree: A Huffman tree.
      uncompressed: A file stream from which you can read the input.
      compressed: A file stream that will receive the tree description
          and the coded input data.
    '''
    bitwriter = bitio.BitWriter(compressed)
    # encode the tree itself
    write_tree(tree, bitwriter)
    # create a dictionary for codes where each code takes the form (bool,bool,bool,...)
    codes = huffman.make_encoding_table(tree)

    buff = bytearray(512) # the buffer in which to read the input
    while True:
        count = uncompressed.readinto(buff)
        for i in range(count):
            for node in codes[buff[i]]:
                if node == True:
                    bitwriter.writebit(1)
                elif node == False:
                    bitwriter.writebit(0)
                else:
                    # if the node is for some reason not stored correctly
                    raise Exception("Nodetype not boolean, found: {}".format(type(node)))

        if count < len(buff): # when there is no more input
            break

    # encode and send an end of message character to finish the message
    for node in codes[None]: # None is the end of message character
        if node == True:
            bitwriter.writebit(1)
        elif node == False:
            bitwriter.writebit(0)
        else:
            # if the node is for some reason not stored correctly
            raise Exception("Nodetype not boolean, found: {}".format(type(node)))

    # write extra bits if needed to fill the last byte
    bitwriter.writebits(0, 8 - bitwriter.bcount)
    bitwriter.flush()
