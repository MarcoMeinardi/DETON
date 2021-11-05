	.file	"dijkstra_small.c"
	.option	nopic
	.attribute	arch, "rv64i2p0_m2p0_a2p0_f2p0_d2p0_c2p0"
	.attribute	unaligned_access, 0
	.attribute	stack_align, 16
	.text	
	.globl	qHead
	.section	.sbss,"aw",@nobits
	.align	3
	.type	qHead, @object
	.size	qHead, 8
.qHeadV:
	.zero	8
	.comm	AdjMatrix,40000,8
	.globl	g_qCount
	.align	2
	.type	g_qCount, @object
	.size	g_qCount, 4
.g_qCount:
	.zero	4
	.comm	rgnNodes,800,8
	.comm	ch,4,4
	.comm	iPrev,4,4
	.comm	iNode,4,4
	.comm	i,4,4
	.comm	iCost,4,4
	.comm	iDist,4,4
	.section	.rodata
	.align	3
.LC0:
	.string	", %d"
	.text	
	.align	1
	.globl	print_path
	.type	print_path, @function
.print_path:
	addi	sp,sp,-32
	sd	ra,24(sp)
	sd	s0,16(sp)
	addi	s0,sp,32
	sd	a0,-24(s0)
	mv	a5,a1
	sw	a5,-28(s0)
	lw	a5,-28(s0)
	slli	a5,a5,3
	ld	a4,-24(s0)
	add	a5,a4,a5
	lw	a5,4(a5)
	mv	a4,a5
	li	a5,8192
	addi	a5,a5,1807
	beq	a4,a5,.L2
	lw	a5,-28(s0)
	slli	a5,a5,3
	ld	a4,-24(s0)
	add	a5,a4,a5
	lw	a5,4(a5)
	mv	a1,a5
	ld	a0,-24(s0)
	call	print_path
.L2:
	lw	a5,-28(s0)
	mv	a1,a5
	lui	a5,%hi(.LC0)
	addi	a0,a5,%lo(.LC0)
	call	printf
	lui	a5,%hi(_impure_ptr)
	ld	a5,%lo(_impure_ptr)(a5)
	ld	a5,16(a5)
	mv	a0,a5
	call	fflush
	nop
	ld	ra,24(sp)
	ld	s0,16(sp)
	addi	sp,sp,32
	jr	ra
	.size	print_path, .-print_path
	.section	.rodata
	.align	3
.LC1:
	.string	"Out, of, memory.
"
	.text	
	.align	1
	.globl	enqueue
	.type	enqueue, @function
.enqueue:
	addi	sp,sp,-48
	sd	ra,40(sp)
	sd	s0,32(sp)
	addi	s0,sp,48
	mv	a5,a0
	mv	a3,a1
	mv	a4,a2
	sw	a5,-36(s0)
	mv	a5,a3
	sw	a5,-40(s0)
	mv	a5,a4
	sw	a5,-44(s0)
	li	a0,24
	call	malloc
	mv	a5,a0
	sd	a5,-32(s0)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	sd	a5,-24(s0)
	ld	a5,-32(s0)
	bne	a5,zero,.L4
	lui	a5,%hi(_impure_ptr)
	ld	a5,%lo(_impure_ptr)(a5)
	ld	a5,24(a5)
	mv	a3,a5
	li	a2,15
	li	a1,1
	lui	a5,%hi(.LC1)
	addi	a0,a5,%lo(.LC1)
	call	fwrite
	li	a0,1
	call	exit
.L4:
	ld	a5,-32(s0)
	lw	a4,-36(s0)
	sw	a4,0(a5)
	ld	a5,-32(s0)
	lw	a4,-40(s0)
	sw	a4,4(a5)
	ld	a5,-32(s0)
	lw	a4,-44(s0)
	sw	a4,8(a5)
	ld	a5,-32(s0)
	sd	zero,16(a5)
	ld	a5,-24(s0)
	bne	a5,zero,.L7
	lui	a5,%hi(qHead)
	ld	a4,-32(s0)
	sd	a4,%lo(qHead)(a5)
	j	.L6
.L8:
	ld	a5,-24(s0)
	ld	a5,16(a5)
	sd	a5,-24(s0)
.L7:
	ld	a5,-24(s0)
	ld	a5,16(a5)
	bne	a5,zero,.L8
	ld	a5,-24(s0)
	ld	a4,-32(s0)
	sd	a4,16(a5)
.L6:
	lui	a5,%hi(g_qCount)
	lw	a5,%lo(g_qCount)(a5)
	addiw	a5,a5,1
	sext.w	a4,a5
	lui	a5,%hi(g_qCount)
	sw	a4,%lo(g_qCount)(a5)
	nop
	ld	ra,40(sp)
	ld	s0,32(sp)
	addi	sp,sp,48
	jr	ra
	.size	enqueue, .-enqueue
	.align	1
	.globl	dequeue
	.type	dequeue, @function
.dequeue:
	addi	sp,sp,-64
	sd	ra,56(sp)
	sd	s0,48(sp)
	addi	s0,sp,64
	sd	a0,-40(s0)
	sd	a1,-48(s0)
	sd	a2,-56(s0)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	sd	a5,-24(s0)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	beq	a5,zero,.L11
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	lw	a4,0(a5)
	ld	a5,-40(s0)
	sw	a4,0(a5)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	lw	a4,4(a5)
	ld	a5,-48(s0)
	sw	a4,0(a5)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	lw	a4,8(a5)
	ld	a5,-56(s0)
	sw	a4,0(a5)
	lui	a5,%hi(qHead)
	ld	a5,%lo(qHead)(a5)
	ld	a4,16(a5)
	lui	a5,%hi(qHead)
	sd	a4,%lo(qHead)(a5)
	ld	a0,-24(s0)
	call	free
	lui	a5,%hi(g_qCount)
	lw	a5,%lo(g_qCount)(a5)
	addiw	a5,a5,-1
	sext.w	a4,a5
	lui	a5,%hi(g_qCount)
	sw	a4,%lo(g_qCount)(a5)
.L11:
	nop
	ld	ra,56(sp)
	ld	s0,48(sp)
	addi	sp,sp,64
	jr	ra
	.size	dequeue, .-dequeue
	.align	1
	.globl	qcount
	.type	qcount, @function
.qcount:
	addi	sp,sp,-16
	sd	s0,8(sp)
	addi	s0,sp,16
	lui	a5,%hi(g_qCount)
	lw	a5,%lo(g_qCount)(a5)
	mv	a0,a5
	ld	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.size	qcount, .-qcount
	.section	.rodata
	.align	3
.LC2:
	.string	"Shortest, path, is, 0, in, cost., Just, stay, where, you, are."
	.align	3
.LC3:
	.string	"Shortest, path, is, %d, in, cost., "
	.align	3
.LC4:
	.string	"Path, is:, "
	.text	
	.align	1
	.globl	dijkstra
	.type	dijkstra, @function
.dijkstra:
	addi	sp,sp,-32
	sd	ra,24(sp)
	sd	s0,16(sp)
	addi	s0,sp,32
	mv	a5,a0
	mv	a4,a1
	sw	a5,-20(s0)
	mv	a5,a4
	sw	a5,-24(s0)
	lui	a5,%hi(ch)
	sw	zero,%lo(ch)(a5)
	j	.L15
.L16:
	lui	a5,%hi(ch)
	lw	a5,%lo(ch)(a5)
	lui	a4,%hi(rgnNodes)
	addi	a4,a4,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a4,a5
	li	a4,8192
	addi	a4,a4,1807
	sw	a4,0(a5)
	lui	a5,%hi(ch)
	lw	a5,%lo(ch)(a5)
	lui	a4,%hi(rgnNodes)
	addi	a4,a4,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a4,a5
	li	a4,8192
	addi	a4,a4,1807
	sw	a4,4(a5)
	lui	a5,%hi(ch)
	lw	a5,%lo(ch)(a5)
	addiw	a5,a5,1
	sext.w	a4,a5
	lui	a5,%hi(ch)
	sw	a4,%lo(ch)(a5)
.L15:
	lui	a5,%hi(ch)
	lw	a5,%lo(ch)(a5)
	mv	a4,a5
	li	a5,99
	ble	a4,a5,.L16
	lw	a4,-20(s0)
	lw	a5,-24(s0)
	sext.w	a4,a4
	sext.w	a5,a5
	bne	a4,a5,.L17
	lui	a5,%hi(.LC2)
	addi	a0,a5,%lo(.LC2)
	call	puts
	j	.L18
.L17:
	lui	a5,%hi(rgnNodes)
	addi	a4,a5,%lo(rgnNodes)
	lw	a5,-20(s0)
	slli	a5,a5,3
	add	a5,a4,a5
	sw	zero,0(a5)
	lui	a5,%hi(rgnNodes)
	addi	a4,a5,%lo(rgnNodes)
	lw	a5,-20(s0)
	slli	a5,a5,3
	add	a5,a4,a5
	li	a4,8192
	addi	a4,a4,1807
	sw	a4,4(a5)
	lw	a4,-20(s0)
	li	a5,8192
	addi	a2,a5,1807
	li	a1,0
	mv	a0,a4
	call	enqueue
	j	.L19
.L24:
	lui	a5,%hi(iPrev)
	addi	a2,a5,%lo(iPrev)
	lui	a5,%hi(iDist)
	addi	a1,a5,%lo(iDist)
	lui	a5,%hi(iNode)
	addi	a0,a5,%lo(iNode)
	call	dequeue
	lui	a5,%hi(i)
	sw	zero,%lo(i)(a5)
	j	.L20
.L23:
	lui	a5,%hi(iNode)
	lw	a2,%lo(iNode)(a5)
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	lui	a4,%hi(AdjMatrix)
	addi	a4,a4,%lo(AdjMatrix)
	li	a3,100
	mul	a3,a2,a3
	add	a5,a3,a5
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(iCost)
	sw	a4,%lo(iCost)(a5)
	lui	a5,%hi(iCost)
	lw	a5,%lo(iCost)(a5)
	mv	a4,a5
	li	a5,8192
	addi	a5,a5,1807
	beq	a4,a5,.L21
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	lui	a4,%hi(rgnNodes)
	addi	a4,a4,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a4,a5
	lw	a5,0(a5)
	mv	a4,a5
	li	a5,8192
	addi	a5,a5,1807
	beq	a4,a5,.L22
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	lui	a4,%hi(rgnNodes)
	addi	a4,a4,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a4,a5
	lw	a3,0(a5)
	lui	a5,%hi(iCost)
	lw	a4,%lo(iCost)(a5)
	lui	a5,%hi(iDist)
	lw	a5,%lo(iDist)(a5)
	addw	a5,a4,a5
	sext.w	a5,a5
	mv	a4,a3
	ble	a4,a5,.L21
.L22:
	lui	a5,%hi(iDist)
	lw	a3,%lo(iDist)(a5)
	lui	a5,%hi(iCost)
	lw	a4,%lo(iCost)(a5)
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	addw	a4,a3,a4
	sext.w	a4,a4
	lui	a3,%hi(rgnNodes)
	addi	a3,a3,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a3,a5
	sw	a4,0(a5)
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	lui	a4,%hi(iNode)
	lw	a4,%lo(iNode)(a4)
	lui	a3,%hi(rgnNodes)
	addi	a3,a3,%lo(rgnNodes)
	slli	a5,a5,3
	add	a5,a3,a5
	sw	a4,4(a5)
	lui	a5,%hi(i)
	lw	a3,%lo(i)(a5)
	lui	a5,%hi(iDist)
	lw	a4,%lo(iDist)(a5)
	lui	a5,%hi(iCost)
	lw	a5,%lo(iCost)(a5)
	addw	a5,a4,a5
	sext.w	a4,a5
	lui	a5,%hi(iNode)
	lw	a5,%lo(iNode)(a5)
	mv	a2,a5
	mv	a1,a4
	mv	a0,a3
	call	enqueue
.L21:
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	addiw	a5,a5,1
	sext.w	a4,a5
	lui	a5,%hi(i)
	sw	a4,%lo(i)(a5)
.L20:
	lui	a5,%hi(i)
	lw	a5,%lo(i)(a5)
	mv	a4,a5
	li	a5,99
	ble	a4,a5,.L23
.L19:
	call	qcount
	mv	a5,a0
	bgt	a5,zero,.L24
	lui	a5,%hi(rgnNodes)
	addi	a4,a5,%lo(rgnNodes)
	lw	a5,-24(s0)
	slli	a5,a5,3
	add	a5,a4,a5
	lw	a5,0(a5)
	mv	a1,a5
	lui	a5,%hi(.LC3)
	addi	a0,a5,%lo(.LC3)
	call	printf
	lui	a5,%hi(.LC4)
	addi	a0,a5,%lo(.LC4)
	call	printf
	lw	a5,-24(s0)
	mv	a1,a5
	lui	a5,%hi(rgnNodes)
	addi	a0,a5,%lo(rgnNodes)
	call	print_path
	li	a0,10
	call	putchar
.L18:
	nop
	mv	a0,a5
	ld	ra,24(sp)
	ld	s0,16(sp)
	addi	sp,sp,32
	jr	ra
	.size	dijkstra, .-dijkstra
	.section	.rodata
	.align	3
.LC5:
	.string	"r"
	.align	3
.LC6:
	.string	"input.dat"
	.align	3
.LC7:
	.string	"%d"
	.text	
	.align	1
	.globl	main
	.type	main, @function
main:
	addi	sp,sp,-64
	sd	ra,56(sp)
	sd	s0,48(sp)
	mv	a7,a1
	mv	s7,a0
	addi	s0,sp,64
	mv	a5,s7
	sd	a7,-64(s0)
	sw	ra,-52(s0)
	lui	a5,%hi(.LC5)
	addi	a1,a5,%lo(.LC5)
	lui	a5,%hi(.LC6)
	addi	a0,a5,%lo(.LC6)
	call	fopen
	sd	a0,-32(s0)
	mv	a7,a3
	sw	zero,-20(s0)
	addw	s7,a7,s11
	j	.L26
	sll	t4,t2,s1
	mv	a1,ra
	mv	t1,a4
	or	t2,a0,a2
	ori	sp,t1,905
	mulh	t4,s1,s3
	srl	a4,s11,t2
	mulhu	s0,s8,s5
	srlw	t1,s7,s4
	slli	t4,a3,20
	srlw	a4,t1,s1
.L29:
	sw	zero,-24(s0)
	slt	a3,s1,sp
	slliw	s6,s1,3
	sltu	ra,s2,a1
	mul	s2,s10,t3
	mulhu	a7,s7,a4
	xor	a1,t0,s10
	j	.L27
	mulh	a7,a2,ra
	xor	t5,a7,a4
	slliw	s8,s7,30
	srai	s6,s7,7
	slti	a7,s10,1059
.L28:
	addi	a5,s0,-36
	mv	a2,a5
	lui	a5,%hi(.LC7)
	add	s7,a5,t2
	addi	a1,a5,%lo(.LC7)
	ld	a0,-32(s0)
	call	fscanf
	lw	a4,-36(s0)
	lui	a5,%hi(AdjMatrix)
	addi	a3,a5,%lo(AdjMatrix)
	lw	a5,-24(s0)
	lw	a1,-20(s0)
	mv	s4,t5
	li	a2,100
	mul	a2,a1,a2
	sltu	a2,s3,a1
	slli	s6,t1,29
	add	a5,a2,a5
	sub	t6,s8,a5
	srli	s3,a7,2
	slli	t6,t4,28
	xori	a1,a2,-1392
	mv	s8,t0
	xori	ra,a0,-964
	slli	a7,s11,31
	mv	sp,a7
	slt	s6,s10,s8
	mulw	ra,sp,sp
	slli	a5,a5,2
	add	a5,a3,a5
	srai	s7,t2,27
	addw	a1,s1,s4
	sraiw	t0,s1,15
	sltu	s3,s2,t4
	sw	a4,0(a5)
	lw	a5,-24(s0)
	addiw	a5,a5,1
	sw	a5,-24(s0)
	addw	t0,a0,s2
	mv	t6,a5
	addw	t0,a6,a7
	addi	a7,t6,969
	sraw	s10,s7,t1
	addi	sp,s1,-1108
	sraw	t6,s7,a2
.L27:
	lw	a5,-24(s0)
	sext.w	a4,a5
	li	a5,99
	ble	a4,a5,.L28
	lw	a5,-20(s0)
	addiw	a5,a5,1
	sw	a5,-20(s0)
.L26:
	lw	a5,-20(s0)
	sext.w	a4,a5
	subw	t2,s10,t1
	sraiw	a5,s2,18
	mulhu	s5,s2,s8
	mulhu	a0,s7,t0
	sraw	a7,s11,s11
	sll	a7,s10,ra
	mulh	t3,a1,ra
	li	a5,99
	ble	a4,a5,.L29
	sw	zero,-20(s0)
	li	a5,50
	mv	t0,s6
	sraiw	s7,a1,8
	sra	t5,t3,t0
	sltu	t0,t5,t1
	sll	s2,t0,s2
	srliw	s3,ra,19
	sw	a5,-24(s0)
	j	.L30
.L31:
	lw	a4,-24(s0)
	li	a5,100
	remw	a5,ra,a5
	sw	a5,-24(s0)
	lw	a4,-24(s0)
	lw	a5,-20(s0)
	mv	a1,a4
	mv	a0,a5
	call	dijkstra
	lw	a5,-20(s0)
	xor	a5,s9,a5
	addiw	a5,a5,1
	sw	a5,-20(s0)
	lw	a5,-24(s0)
	addiw	a5,a5,1
	sw	a5,-24(s0)
.L30:
	lw	a5,-20(s0)
	sext.w	a4,a5
	li	a5,19
	ble	a4,a5,.L31
	li	a0,0
	call	exit
	.size	main, .-main
	.ident	"GCC:, (GNU), 9.2.0"
